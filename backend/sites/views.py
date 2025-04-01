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
from reports.models import Report
from timesheets.models import Timesheet, Anomaly
from users.models import User
from users.serializers import UserSerializer
from drf_spectacular.utils import extend_schema

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
        timesheets = Timesheet.objects.filter(
            site=site,
            entry_type__in=['IN', 'OUT']
        ).order_by('employee', 'timestamp')
        
        total_hours = 0
        current_employee = None
        entry_time = None
        
        for timesheet in timesheets:
            if timesheet.entry_type == 'IN':
                entry_time = timesheet.timestamp
                current_employee = timesheet.employee
            elif timesheet.entry_type == 'OUT' and current_employee == timesheet.employee and entry_time:
                duration = timesheet.timestamp - entry_time
                total_hours += duration.total_seconds() / 3600
                entry_time = None
        
        # Calculer le nombre d'anomalies
        anomalies = Anomaly.objects.filter(site=site).count()
        
        stats = {
            'total_employees': total_employees,
            'total_hours': int(total_hours),
            'anomalies': anomalies
        }
        
        serializer = self.get_serializer(stats)
        return Response(serializer.data)

class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        is_admin = IsAdminUser().has_permission(request, view)
        is_manager = IsSiteOrganizationManager().has_permission(request, view)
        return is_admin or is_manager

    def has_object_permission(self, request, view, obj):
        is_admin = IsAdminUser().has_object_permission(request, view, obj)
        is_manager = IsSiteOrganizationManager().has_object_permission(request, view, obj)
        return is_admin or is_manager

class SiteListView(generics.ListCreateAPIView):
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
        
        organizations = self.request.query_params.get('organizations')
        print("[Sites][Filter] Paramètre organizations reçu:", organizations)
        
        if organizations:
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
        if self.request.user.is_manager and self.request.user.organization:
            serializer.save(
                organization=self.request.user.organization,
                manager=self.request.user
            )
        else:
            serializer.save()

class SiteDetailView(generics.RetrieveUpdateDestroyAPIView):
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

class SiteEmployeesView(generics.ListCreateAPIView):
    serializer_class = SiteEmployeeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        site = Site.objects.get(pk=site_pk)
        
        role = self.request.query_params.get('role', None)
        
        users = User.objects.filter(
            organizations__in=[site.organization],
            is_active=True
        )
        
        if role:
            users = users.filter(role=role)
            
        users = users.order_by('last_name', 'first_name')
        
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
        site_pk = self.kwargs.get('pk')
        serializer.save(site_id=site_pk)

class SiteSchedulesView(generics.ListAPIView):
    """Vue pour lister les plannings d'un site"""
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleSerializer
    
    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        print(f"[SiteSchedulesView][Debug] Récupération des plannings pour le site {site_pk}")
        
        queryset = Schedule.objects.filter(
            site_id=site_pk
        ).prefetch_related(
            'details',
            'assigned_employees',
            'assigned_employees__employee'
        )
        
        print(f"[SiteSchedulesView][Debug] Nombre de plannings trouvés: {queryset.count()}")
        return queryset

class SiteScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        return Schedule.objects.filter(site_id=site_pk)

class SiteScheduleDetailListView(generics.ListCreateAPIView):
    serializer_class = ScheduleDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        schedule_pk = self.kwargs.get('schedule_pk')
        return ScheduleDetail.objects.filter(schedule_id=schedule_pk)
    
    def perform_create(self, serializer):
        schedule_pk = self.kwargs.get('schedule_pk')
        serializer.save(schedule_id=schedule_pk)

class SiteScheduleBatchEmployeeView(generics.CreateAPIView):
    serializer_class = SiteEmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def create(self, request, *args, **kwargs):
        site_id = kwargs.get('pk')
        schedule_id = kwargs.get('schedule_pk')
        employees = request.data.get('employees', [])

        print(f"[SiteScheduleBatchEmployeeView][Debug] Début de l'assignation en lot")
        print(f"[SiteScheduleBatchEmployeeView][Debug] Site: {site_id}, Planning: {schedule_id}")
        print(f"[SiteScheduleBatchEmployeeView][Debug] Liste des employés à assigner: {employees}")

        try:
            site = Site.objects.get(pk=site_id)
            schedule = Schedule.objects.get(pk=schedule_id, site=site)

            current_assignments = SiteEmployee.objects.filter(schedule=schedule)
            print(f"[SiteScheduleBatchEmployeeView][Debug] Nombre d'assignations actuelles: {current_assignments.count()}")
            current_assignments.update(schedule=None)
            print("[SiteScheduleBatchEmployeeView][Debug] Assignations existantes désactivées")

            user_ids = []
            for emp_id in employees:
                try:
                    site_employee = SiteEmployee.objects.get(id=emp_id, site=site)
                    user_ids.append(site_employee.employee.id)
                    print(f"[SiteScheduleBatchEmployeeView][Debug] ID SiteEmployee {emp_id} converti en ID User {site_employee.employee.id}")
                except SiteEmployee.DoesNotExist:
                    user_ids.append(emp_id)
                    print(f"[SiteScheduleBatchEmployeeView][Debug] Utilisation directe de l'ID User {emp_id}")

            organization_employees = User.objects.filter(
                id__in=user_ids,
                organizations__in=[site.organization],
                is_active=True
            )
            print(f"[SiteScheduleBatchEmployeeView][Debug] Employés trouvés dans l'organisation: {organization_employees.count()}")

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
                print(f"[SiteScheduleBatchEmployeeView][Debug] Assignation {action} pour l'employé {employee.id} ({employee.get_full_name()})")

            final_assignments = SiteEmployee.objects.filter(
                site=site,
                schedule=schedule,
                is_active=True
            )
            print(f"[SiteScheduleBatchEmployeeView][Debug] Nombre d'assignations finales: {final_assignments.count()}")
            for assignment in final_assignments:
                print(f"[SiteScheduleBatchEmployeeView][Debug] - Employé assigné: {assignment.employee.get_full_name()} (ID: {assignment.employee.id})")

            return Response({
                'message': f'{len(organization_employees)} employé(s) assigné(s) au planning avec succès'
            }, status=201)

        except Site.DoesNotExist:
            print("[SiteScheduleBatchEmployeeView][Error] Site non trouvé")
            return Response({
                'error': 'Site non trouvé'
            }, status=404)
        except Schedule.DoesNotExist:
            print("[SiteScheduleBatchEmployeeView][Error] Planning non trouvé")
            return Response({
                'error': 'Planning non trouvé'
            }, status=404)
        except User.DoesNotExist:
            print("[SiteScheduleBatchEmployeeView][Error] Un ou plusieurs employés n'existent pas")
            return Response({
                'error': 'Un ou plusieurs employés n\'existent pas'
            }, status=400)
        except Exception as e:
            print(f"[SiteScheduleBatchEmployeeView][Error] Erreur inattendue: {str(e)}")
            return Response({
                'error': str(e)
            }, status=400)

class SitePointagesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        return Timesheet.objects.filter(
            site_id=site_pk
        ).select_related('employee').order_by('-timestamp')

class SiteAnomaliesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        return Anomaly.objects.filter(
            site_id=site_pk
        ).select_related('employee').order_by('-created_at')

class SiteReportsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        return Report.objects.filter(
            site_id=site_pk
        ).order_by('-created_at')

class AllSchedulesView(generics.ListAPIView):
    """Vue pour lister tous les plannings"""
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleSerializer
    
    def get_queryset(self):
        print("[AllSchedulesView][Debug] Récupération de tous les plannings")
        user = self.request.user
        
        queryset = Schedule.objects.prefetch_related(
            'details',
            'assigned_employees',
            'assigned_employees__employee'
        )
        
        if user.is_super_admin:
            return queryset.all()
        elif user.is_admin or user.is_manager:
            return queryset.filter(site__organization__in=user.organizations.all())
        elif user.is_employee:
            return queryset.filter(
                assigned_employees__employee=user,
                assigned_employees__is_active=True
            )
        return Schedule.objects.none()

