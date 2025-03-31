from rest_framework import generics, permissions, viewsets, serializers
from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
from .serializers import (
    SiteSerializer, ScheduleSerializer, ScheduleDetailSerializer, 
    SiteEmployeeSerializer
)
from .permissions import IsSiteOrganizationManager
from django.db import models
from django.db.models import Count, Q, F, ExpressionWrapper, fields
from django.db.models.functions import ExtractHour, ExtractMinute
from timesheets.models import Timesheet, Anomaly
from users.models import User
from users.serializers import UserSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from datetime import timedelta

class SiteStatisticsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    total_hours = serializers.IntegerField()
    anomalies = serializers.IntegerField()

class SiteStatisticsView(generics.RetrieveAPIView):
    serializer_class = SiteStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Site.objects.all()
    
    @extend_schema(
        responses={200: SiteStatisticsSerializer},
        description="Obtenir les statistiques d'un site"
    )
    def get(self, request, *args, **kwargs):
        site = self.get_object()
        
        # Calculer les statistiques
        total_employees = SiteEmployee.objects.filter(site=site, is_active=True).count()
        
        # Calculer le total des heures en utilisant les entrées/sorties
        # On groupe les pointages par paire (entrée/sortie)
        timesheets = Timesheet.objects.filter(
            site=site,
            entry_type__in=['IN', 'OUT']  # Seulement les entrées et sorties
        ).order_by('employee', 'timestamp')
        
        total_hours = 0
        current_employee = None
        entry_time = None
        
        for timesheet in timesheets:
            if timesheet.entry_type == 'IN':
                entry_time = timesheet.timestamp
                current_employee = timesheet.employee
            elif timesheet.entry_type == 'OUT' and current_employee == timesheet.employee and entry_time:
                # Calculer la durée entre l'entrée et la sortie
                duration = timesheet.timestamp - entry_time
                total_hours += duration.total_seconds() / 3600  # Convertir en heures
                entry_time = None
        
        # Calculer le nombre d'anomalies
        anomalies = Anomaly.objects.filter(
            site=site
        ).count()
        
        stats = {
            'total_employees': total_employees,
            'total_hours': int(total_hours),  # Convertir en entier pour simplifier
            'anomalies': anomalies
        }
        
        serializer = self.get_serializer(stats)
        return Response(serializer.data)

class IsAdminOrManager(BasePermission):
    """Permission composée pour autoriser les admin ou les managers d'organisation"""
    def has_permission(self, request, view):
        is_admin = IsAdminUser().has_permission(request, view)
        is_manager = IsSiteOrganizationManager().has_permission(request, view)
        return is_admin or is_manager

    def has_object_permission(self, request, view, obj):
        is_admin = IsAdminUser().has_object_permission(request, view, obj)
        is_manager = IsSiteOrganizationManager().has_object_permission(request, view, obj)
        return is_admin or is_manager

class SiteListView(generics.ListCreateAPIView):
    """Vue pour lister tous les sites et en créer de nouveaux"""
    serializer_class = SiteSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        user = self.request.user
        base_queryset = Site.objects.prefetch_related(
            'schedules',
            'schedules__assigned_employees',
            'schedules__assigned_employees__employee'
        )
        
        # Récupérer le paramètre organizations de la requête
        organizations = self.request.query_params.get('organizations')
        print("[Sites][Filter] Paramètre organizations reçu:", organizations)
        
        if organizations:
            # Convertir la chaîne en liste d'IDs
            organization_ids = [int(org_id) for org_id in organizations.split(',')]
            print("[Sites][Filter] IDs des organisations:", organization_ids)
            base_queryset = base_queryset.filter(organization_id__in=organization_ids)
            print("[Sites][Count] Nombre de sites après filtre:", base_queryset.count())
        
        if user.is_super_admin:
            return base_queryset
        elif user.is_admin or user.is_manager:
            return base_queryset.filter(organization__in=user.organizations.all())
        elif user.is_employee:
            return base_queryset.filter(employees__employee=user, employees__is_active=True)
        return Site.objects.none()
    
    def perform_create(self, serializer):
        # Si l'utilisateur est un manager, associer le site à son organisation
        if self.request.user.is_manager and self.request.user.organization:
            serializer.save(
                organization=self.request.user.organization,
                manager=self.request.user  # Le manager créateur devient le manager du site
            )
        else:
            serializer.save()

class SiteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un site spécifique"""
    serializer_class = SiteSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        user = self.request.user
        base_queryset = Site.objects.prefetch_related(
            'schedules',
            'schedules__assigned_employees',
            'schedules__assigned_employees__employee'
        )
        
        if user.is_super_admin:
            return base_queryset.all()
        elif user.is_admin or user.is_manager:
            return base_queryset.filter(organization__in=user.organizations.all())
        elif user.is_employee:
            return base_queryset.filter(employees__employee=user, employees__is_active=True)
        return Site.objects.none()

class ScheduleListView(generics.ListCreateAPIView):
    """Vue pour lister tous les plannings d'un site et en créer de nouveaux"""
    serializer_class = ScheduleSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return Schedule.objects.filter(site_id=site_pk)
    
    def perform_create(self, serializer):
        site_pk = self.kwargs.get('site_pk')
        serializer.save(site_id=site_pk)

class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un planning spécifique"""
    serializer_class = ScheduleSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return Schedule.objects.filter(site_id=site_pk)

class ScheduleDetailListView(generics.ListCreateAPIView):
    """Vue pour lister tous les détails d'un planning et en créer de nouveaux"""
    serializer_class = ScheduleDetailSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        schedule_pk = self.kwargs.get('schedule_pk')
        return ScheduleDetail.objects.filter(schedule_id=schedule_pk)
    
    def perform_create(self, serializer):
        schedule_pk = self.kwargs.get('schedule_pk')
        serializer.save(schedule_id=schedule_pk)

class SiteEmployeeListView(generics.ListCreateAPIView):
    """Vue pour lister tous les employés d'un site et en ajouter de nouveaux"""
    serializer_class = SiteEmployeeSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        site = Site.objects.get(pk=site_pk)
        
        # Récupérer le paramètre role de la requête
        role = self.request.query_params.get('role', None)
        
        # Récupérer tous les utilisateurs de l'organisation
        users = User.objects.filter(
            organizations__in=[site.organization],
            is_active=True
        )
        
        # Filtrer par rôle si spécifié
        if role:
            users = users.filter(role=role)
            
        users = users.order_by('last_name', 'first_name')
        
        # Pour chaque utilisateur, créer ou récupérer une entrée SiteEmployee
        site_employees = []
        for user in users:
            site_employee, created = SiteEmployee.objects.get_or_create(
                site_id=site_pk,
                employee=user,
                defaults={'is_active': True}
            )
            site_employees.append(site_employee)
        
        return SiteEmployee.objects.filter(
            site_id=site_pk,
            employee__in=users
        )
    
    def perform_create(self, serializer):
        site_pk = self.kwargs.get('site_pk')
        serializer.save(site_id=site_pk)

class SiteEmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un employé d'un site"""
    serializer_class = SiteEmployeeSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return SiteEmployee.objects.filter(site_id=site_pk)

class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]

class GlobalScheduleListView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print("[GlobalScheduleListView][Debug] Début de get_queryset")
        
        queryset = Schedule.objects.prefetch_related(
            models.Prefetch(
                'assigned_employees',
                queryset=SiteEmployee.objects.filter(is_active=True, schedule__isnull=False).select_related('employee')
            )
        ).select_related('site')
        
        print(f"[GlobalScheduleListView][Debug] Nombre de plannings trouvés: {queryset.count()}")
        
        # Filtrer par site si spécifié
        site = self.request.query_params.get('site')
        if site:
            print(f"[GlobalScheduleListView][Debug] Filtrage par site: {site}")
            queryset = queryset.filter(site_id=site)
            print(f"[GlobalScheduleListView][Debug] Nombre de plannings après filtre site: {queryset.count()}")
        
        # Filtrer par type de planning si spécifié
        schedule_type = self.request.query_params.get('schedule_type')
        if schedule_type:
            print(f"[GlobalScheduleListView][Debug] Filtrage par type: {schedule_type}")
            queryset = queryset.filter(schedule_type=schedule_type)
            print(f"[GlobalScheduleListView][Debug] Nombre de plannings après filtre type: {queryset.count()}")
        
        # Filtrer selon le rôle de l'utilisateur
        user = self.request.user
        print(f"[GlobalScheduleListView][Debug] Utilisateur: {user.username} (role: {user.role})")
        
        if user.is_super_admin:
            print("[GlobalScheduleListView][Debug] Utilisateur super admin, pas de filtre supplémentaire")
            return queryset
        elif user.is_admin or user.is_manager:
            print("[GlobalScheduleListView][Debug] Utilisateur admin/manager, filtrage par organisation")
            queryset = queryset.filter(site__organization__in=user.organizations.all())
        elif user.is_employee:
            print("[GlobalScheduleListView][Debug] Utilisateur employé, filtrage par site assigné")
            queryset = queryset.filter(site__employees__employee=user, site__employees__is_active=True)
        
        print(f"[GlobalScheduleListView][Debug] Nombre final de plannings: {queryset.count()}")
        
        # Vérifier les employés assignés pour chaque planning
        for schedule in queryset:
            employees = SiteEmployee.objects.filter(
                site=schedule.site,
                schedule=schedule,
                is_active=True
            )
            print(f"[GlobalScheduleListView][Debug] Planning {schedule.id} - Employés assignés: {employees.count()}")
            for employee in employees:
                print(f"[GlobalScheduleListView][Debug] - Employé: {employee.employee.get_full_name()} (ID: {employee.employee.id})")
        
        return queryset

    def perform_create(self, serializer):
        schedule = serializer.save()
        site = schedule.site

        # Vérifier s'il y a des employés de l'organisation qui ne sont pas encore assignés au site
        organization_employees = User.objects.filter(
            organizations__in=[site.organization],
            is_active=True
        ).exclude(
            assigned_sites__site=site,
            assigned_sites__is_active=True
        )

        # Pour chaque employé trouvé, créer une assignation au site
        for employee in organization_employees:
            SiteEmployee.objects.create(
                site=site,
                employee=employee,
                schedule=schedule,
                is_active=True
            )

        return schedule

class GlobalScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

class SiteUnassignedEmployeesView(generics.ListAPIView):
    """Vue pour lister tous les employés non assignés à un site spécifique"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
            
        site = Site.objects.get(pk=self.kwargs['pk'])
        
        # Récupérer les employés qui :
        # 1. Sont dans la même organisation que le site
        # 2. Ne sont pas déjà assignés à ce site
        # 3. Sont actifs
        return User.objects.filter(
            organizations__in=[site.organization],
            is_active=True
        ).exclude(
            id__in=SiteEmployee.objects.filter(
                site=site,
                is_active=True
            ).values_list('employee_id', flat=True)
        ).order_by('last_name', 'first_name')

class ScheduleBatchEmployeeView(generics.CreateAPIView):
    """Vue pour ajouter des employés en lot à un planning"""
    serializer_class = SiteEmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def create(self, request, *args, **kwargs):
        site_id = kwargs.get('site_pk')
        schedule_id = kwargs.get('schedule_pk')
        employees = request.data.get('employees', [])

        print(f"[ScheduleBatchEmployeeView][Debug] Début de l'assignation en lot")
        print(f"[ScheduleBatchEmployeeView][Debug] Site: {site_id}, Planning: {schedule_id}")
        print(f"[ScheduleBatchEmployeeView][Debug] Liste des employés à assigner: {employees}")

        try:
            site = Site.objects.get(pk=site_id)
            schedule = Schedule.objects.get(pk=schedule_id, site=site)

            # Désactiver les assignations existantes pour ce planning
            current_assignments = SiteEmployee.objects.filter(schedule=schedule)
            print(f"[ScheduleBatchEmployeeView][Debug] Nombre d'assignations actuelles: {current_assignments.count()}")
            current_assignments.update(schedule=None)
            print("[ScheduleBatchEmployeeView][Debug] Assignations existantes désactivées")

            # Convertir les IDs SiteEmployee en IDs User si nécessaire
            user_ids = []
            for emp_id in employees:
                try:
                    # Essayer de récupérer l'ID de l'utilisateur à partir de SiteEmployee
                    site_employee = SiteEmployee.objects.get(id=emp_id, site=site)
                    user_ids.append(site_employee.employee.id)
                    print(f"[ScheduleBatchEmployeeView][Debug] ID SiteEmployee {emp_id} converti en ID User {site_employee.employee.id}")
                except SiteEmployee.DoesNotExist:
                    # Si ce n'est pas un ID SiteEmployee, supposer que c'est un ID User
                    user_ids.append(emp_id)
                    print(f"[ScheduleBatchEmployeeView][Debug] Utilisation directe de l'ID User {emp_id}")

            # Récupérer tous les employés de l'organisation
            organization_employees = User.objects.filter(
                id__in=user_ids,
                organizations__in=[site.organization],
                is_active=True
            )
            print(f"[ScheduleBatchEmployeeView][Debug] Employés trouvés dans l'organisation: {organization_employees.count()}")

            # Pour chaque employé, créer ou mettre à jour son assignation
            for employee in organization_employees:
                site_employee, created = SiteEmployee.objects.get_or_create(
                    site=site,
                    employee=employee,
                    defaults={'is_active': True}
                )
                site_employee.schedule = schedule
                site_employee.is_active = True
                site_employee.save()

                action = "créée" if created else "mise à jour"
                print(f"[ScheduleBatchEmployeeView][Debug] Assignation {action} pour l'employé {employee.id} ({employee.get_full_name()})")

            # Vérifier les assignations finales
            final_assignments = SiteEmployee.objects.filter(
                site=site,
                schedule=schedule,
                is_active=True
            )
            print(f"[ScheduleBatchEmployeeView][Debug] Nombre d'assignations finales: {final_assignments.count()}")
            for assignment in final_assignments:
                print(f"[ScheduleBatchEmployeeView][Debug] - Employé assigné: {assignment.employee.get_full_name()} (ID: {assignment.employee.id})")

            return Response({
                'message': f'{len(organization_employees)} employé(s) assigné(s) au planning avec succès'
            }, status=201)

        except Site.DoesNotExist:
            print("[ScheduleBatchEmployeeView][Error] Site non trouvé")
            return Response({
                'error': 'Site non trouvé'
            }, status=404)
        except Schedule.DoesNotExist:
            print("[ScheduleBatchEmployeeView][Error] Planning non trouvé")
            return Response({
                'error': 'Planning non trouvé'
            }, status=404)
        except User.DoesNotExist:
            print("[ScheduleBatchEmployeeView][Error] Un ou plusieurs employés n'existent pas")
            return Response({
                'error': 'Un ou plusieurs employés n\'existent pas'
            }, status=400)
        except Exception as e:
            print(f"[ScheduleBatchEmployeeView][Error] Erreur inattendue: {str(e)}")
            return Response({
                'error': str(e)
            }, status=400)

