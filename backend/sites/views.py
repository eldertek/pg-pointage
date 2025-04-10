"""Vues pour les sites"""
# Third party imports
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers
from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

# Django imports
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db import models, IntegrityError, DatabaseError
from django.core.exceptions import ValidationError

# First party imports
from reports.models import Report
from reports.serializers import ReportSerializer
from timesheets.models import Timesheet, Anomaly
from timesheets.serializers import TimesheetSerializer, AnomalySerializer
from users.models import User
from users.serializers import UserSerializer

# Local imports
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
from .serializers import (
    SiteSerializer, ScheduleSerializer, ScheduleDetailSerializer,
    SiteEmployeeSerializer, SiteStatisticsSerializer
)
from .permissions import IsSiteOrganizationManager


class CustomPageNumberPagination(PageNumberPagination):
    """Pagination personnalisée pour les listes"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


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
        total_employees = SiteEmployee.objects.filter(
            site=site, is_active=True).count()

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
            'schedules__schedule_employees',
            'schedules__schedule_employees__employee'
        )

        organizations = self.request.query_params.get('organizations')
        print("[Sites][Filter] Paramètre organizations reçu:", organizations)

        if organizations:
            organization_ids = [int(org_id)
                                for org_id in organizations.split(',')]
            print("[Sites][Filter] IDs des organisations:", organization_ids)
            base_queryset = base_queryset.filter(
                organization_id__in=organization_ids)
            print("[Sites][Count] Nombre de sites après filtre:",
                  base_queryset.count())

        if user.is_super_admin:
            return base_queryset
        elif user.is_admin or user.is_manager:
            return base_queryset.filter(organization__in=user.organizations.all())
        elif user.is_employee:
            return base_queryset.filter(site_employees__employee=user, site_employees__is_active=True)
        return Site.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_manager and self.request.user.organization:
            serializer.save(organization=self.request.user.organization)
        else:
            serializer.save()


class SiteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]
    queryset = Site.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user

        # Super admin peut tout voir
        if user.is_super_admin:
            return obj

        # Admin et Manager peuvent voir les sites de leurs organisations
        if user.is_admin or user.is_manager:
            if not user.organizations.filter(sites=obj).exists():
                raise PermissionDenied("Vous n'avez pas accès à ce site")

        # Employé ne peut voir que les sites auxquels il est assigné
        elif user.is_employee:
            if not (
                user.organizations.filter(id=obj.organization.id).exists() and
                user.employee_sites.filter(site=obj, is_active=True).exists()
            ):
                raise PermissionDenied("Vous n'avez pas accès à ce site")

        return obj


class SiteEmployeesView(generics.ListCreateAPIView):
    serializer_class = SiteEmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        try:
            site = Site.objects.get(pk=site_pk)

            # Vérifier les permissions
            user = self.request.user
            if not user.is_super_admin:
                if user.is_admin or user.is_manager:
                    if not user.organizations.filter(sites=site).exists():
                        raise PermissionDenied(
                            "Vous n'avez pas accès à ce site")
                elif user.is_employee:
                    if not user.employee_sites.filter(site=site, is_active=True).exists():
                        raise PermissionDenied(
                            "Vous n'avez pas accès à ce site")

            # Récupérer le rôle demandé dans les paramètres de requête
            role = self.request.query_params.get('role', None)

            # Base de la requête pour les utilisateurs
            base_query = models.Q(
                organizations__in=[site.organization],
                is_active=True,
                employee_sites__site=site,
                employee_sites__is_active=True
            )

            # Ajouter le manager du site s'il existe
            if site.manager:
                base_query |= models.Q(id=site.manager.id, is_active=True)

            users = User.objects.filter(base_query)

            # Appliquer le filtre de rôle si spécifié
            if role:
                users = users.filter(role=role)

            # Ordonner les résultats
            users = users.order_by('last_name', 'first_name').distinct()

            print(f"[SiteEmployeesView][Debug] Site: {site.name}")
            print(
                f"[SiteEmployeesView][Debug] Organisation: {site.organization.name}")
            print(
                f"[SiteEmployeesView][Debug] Manager du site: {site.manager.get_full_name() if site.manager else 'Aucun'}")
            print(f"[SiteEmployeesView][Debug] Rôle filtré: {role}")
            print(
                f"[SiteEmployeesView][Debug] Nombre d'employés trouvés: {users.count()}")

            # Créer ou récupérer les SiteEmployee pour tous les utilisateurs
            site_employees = []
            for user in users:
                # Vérifier s'il existe déjà des SiteEmployee pour ce site et cet employé
                existing_site_employees = SiteEmployee.objects.filter(
                    site=site,
                    employee=user
                )
                count = existing_site_employees.count()
                print(f"[SiteEmployeesView][Debug] Trouvé {count} SiteEmployee pour l'utilisateur {user.id} sur le site {site.id}")

                if existing_site_employees.exists():
                    # Utiliser le premier SiteEmployee actif ou le premier de la liste
                    active_site_employees = existing_site_employees.filter(is_active=True)
                    active_count = active_site_employees.count()
                    print(f"[SiteEmployeesView][Debug] Dont {active_count} actifs")

                    if active_site_employees.exists():
                        site_employee = active_site_employees.first()
                        print(f"[SiteEmployeesView][Debug] Utilisation du SiteEmployee actif {site_employee.id}")
                    else:
                        site_employee = existing_site_employees.first()
                        print(f"[SiteEmployeesView][Debug] Activation du SiteEmployee {site_employee.id}")
                        site_employee.is_active = True
                        site_employee.save()
                else:
                    # Créer un nouveau SiteEmployee si aucun n'existe
                    print(f"[SiteEmployeesView][Debug] Création d'un nouveau SiteEmployee pour l'utilisateur {user.id} sur le site {site.id}")
                    site_employee = SiteEmployee.objects.create(
                        site=site,
                        employee=user,
                        is_active=True
                    )
                    print(f"[SiteEmployeesView][Debug] Nouveau SiteEmployee créé avec ID {site_employee.id}")

                site_employees.append(site_employee.id)

            return SiteEmployee.objects.filter(
                id__in=site_employees
            ).select_related('employee', 'schedule')

        except Site.DoesNotExist:
            print(f"[SiteEmployeesView][Error] Site {site_pk} non trouvé")
            return SiteEmployee.objects.none()
        except (ValidationError, IntegrityError, DatabaseError, PermissionError) as exc:
            print(f"[SiteEmployeesView][Error] Erreur de base de données: {str(exc)}")
            return SiteEmployee.objects.none()

    def perform_create(self, serializer):
        site_pk = self.kwargs.get('pk')
        try:
            site = Site.objects.get(pk=site_pk)

            # Vérifier les permissions
            user = self.request.user
            if not user.is_super_admin:
                if user.is_admin or user.is_manager:
                    if not user.organizations.filter(sites=site).exists():
                        raise PermissionDenied(
                            "Vous n'avez pas accès à ce site")
                elif user.is_employee:
                    if not user.employee_sites.filter(site=site, is_active=True).exists():
                        raise PermissionDenied(
                            "Vous n'avez pas accès à ce site")

            # Vérifier que l'employé appartient à l'organisation du site
            employee = serializer.validated_data['employee']
            if not employee.organizations.filter(id=site.organization.id).exists():
                raise serializers.ValidationError({
                    'employee': 'L\'employé doit appartenir à l\'organisation du site'
                })

            # Vérifier que l'employé a un planning associé au site
            if not Schedule.objects.filter(site=site, schedule_employees__employee=employee).exists():
                raise serializers.ValidationError({
                    'employee': 'L\'employé doit être associé à un planning du site'
                })

            serializer.save(site=site)

        except Site.DoesNotExist as exc:
            raise serializers.ValidationError({
                'site': 'Site non trouvé'
            }) from exc


class SiteSchedulesView(generics.ListCreateAPIView):
    """Vue pour lister et créer les plannings d'un site"""
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        print(
            f"[SiteSchedulesView][Debug] Récupération des plannings pour le site {site_pk}")

        queryset = Schedule.objects.filter(
            site_id=site_pk
        ).prefetch_related(
            'details',
            'schedule_employees',
            'schedule_employees__employee'
        )

        print(
            f"[SiteSchedulesView][Debug] Nombre de plannings trouvés: {queryset.count()}")
        return queryset

    def perform_create(self, serializer):
        site_pk = self.kwargs.get('pk')
        print(
            f"[SiteSchedulesView][Create] Création d'un planning pour le site {site_pk}")
        serializer.save(site_id=site_pk)


class SiteScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour gérer les détails d'un planning d'un site"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        schedule_pk = self.kwargs.get('schedule_pk')

        if schedule_pk:  # URL de type /sites/<pk>/schedules/<schedule_pk>/
            print(
                f"[SiteScheduleDetailView][Debug] Recherche du planning {schedule_pk} pour le site {site_pk}")
            return Schedule.objects.filter(site_id=site_pk)
        else:  # URL de type /schedules/<pk>/
            print(
                f"[SiteScheduleDetailView][Debug] Recherche du planning {site_pk}")
            return Schedule.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        schedule_pk = self.kwargs.get('schedule_pk', self.kwargs.get('pk'))

        if self.kwargs.get('pk') and self.kwargs.get('schedule_pk'):
            # Pour /sites/<pk>/schedules/<schedule_pk>/
            obj = queryset.filter(id=schedule_pk).first()
        else:
            # Pour /schedules/<pk>/
            obj = queryset.filter(id=schedule_pk).first()

        if not obj:
            print(
                f"[SiteScheduleDetailView][Error] Planning {schedule_pk} non trouvé")
            raise Http404(f"Planning {schedule_pk} non trouvé")

        print(f"[SiteScheduleDetailView][Debug] Planning trouvé: {obj.id}")
        return obj

    def perform_update(self, serializer):
        print("[SiteScheduleDetailView][Update] Début de la mise à jour")
        print(
            f"[SiteScheduleDetailView][Update] Données reçues: {self.request.data}")
        try:
            instance = serializer.save()
            print(
                f"[SiteScheduleDetailView][Update] Planning mis à jour avec succès: {instance.id}")
            return instance
        except (ValidationError, IntegrityError) as exc:
            print(
                f"[SiteScheduleDetailView][Error] Erreur lors de la mise à jour: {str(exc)}")
            raise exc


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

        print("[SiteScheduleBatchEmployeeView][Debug] Début de l'assignation en lot")
        print(f"[SiteScheduleBatchEmployeeView][Debug] Site: {site_id}, Planning: {schedule_id}")
        print(f"[SiteScheduleBatchEmployeeView][Debug] Liste des employés à assigner: {employees}")
        print(f"[SiteScheduleBatchEmployeeView][Debug] Données complètes reçues: {request.data}")

        try:
            site = Site.objects.get(pk=site_id)
            schedule = Schedule.objects.get(pk=schedule_id, site=site)

            print(f"[SiteScheduleBatchEmployeeView][Debug] Site trouvé: {site.name} (ID: {site.id})")
            print(f"[SiteScheduleBatchEmployeeView][Debug] Organisation du site: {site.organization.name} (ID: {site.organization.id})")
            print(f"[SiteScheduleBatchEmployeeView][Debug] Planning trouvé: {schedule.id} (Type: {schedule.schedule_type})")

            user_ids = []
            for emp_id in employees:
                try:
                    # Essayer d'abord de vérifier si c'est un ID d'utilisateur valide
                    try:
                        user = User.objects.get(id=emp_id)
                        user_ids.append(emp_id)
                        print(f"[SiteScheduleBatchEmployeeView][Debug] Utilisation directe de l'ID User BDD={emp_id}, employee_id={user.employee_id}, nom={user.get_full_name()}")
                        continue  # Passer à l'itération suivante si l'utilisateur est trouvé
                    except User.DoesNotExist:
                        # Si ce n'est pas un ID d'utilisateur, continuer avec les autres vérifications
                        pass

                    # Vérifier si c'est un ID de SiteEmployee
                    site_employee = SiteEmployee.objects.get(id=emp_id, site=site)
                    user_ids.append(site_employee.employee.id)
                    print(f"[SiteScheduleBatchEmployeeView][Debug] ID SiteEmployee {emp_id} converti en ID User BDD={site_employee.employee.id}, employee_id={site_employee.employee.employee_id}, nom={site_employee.employee.get_full_name()}")
                except SiteEmployee.DoesNotExist:
                    print(f"[SiteScheduleBatchEmployeeView][Warning] ID {emp_id} ne correspond ni à un User ni à un SiteEmployee")
                    # Essayer de trouver l'utilisateur par son employee_id
                    try:
                        user = User.objects.get(employee_id=f"U{emp_id:05d}")
                        user_ids.append(user.id)
                        print(f"[SiteScheduleBatchEmployeeView][Debug] ID employee_id=U{emp_id:05d} converti en ID User BDD={user.id}, nom={user.get_full_name()}")
                    except User.DoesNotExist:
                        print(f"[SiteScheduleBatchEmployeeView][Warning] Aucun utilisateur trouvé avec employee_id=U{emp_id:05d}")

            # Vérifier les employés existants pour ce planning
            existing_assignments = SiteEmployee.objects.filter(
                site=site,
                schedule=schedule,
                is_active=True
            )
            print(f"[SiteScheduleBatchEmployeeView][Debug] Assignations existantes pour ce planning: {existing_assignments.count()}")
            for assignment in existing_assignments:
                print(f"[SiteScheduleBatchEmployeeView][Debug] - Déjà assigné: ID BDD={assignment.employee.id}, employee_id={assignment.employee.employee_id}, nom={assignment.employee.get_full_name()}")

            # Récupérer les employés de l'organisation correspondant aux IDs
            organization_employees = User.objects.filter(
                id__in=user_ids,
                organizations__in=[site.organization],
                is_active=True
            )
            print(f"[SiteScheduleBatchEmployeeView][Debug] Employés trouvés dans l'organisation: {organization_employees.count()}")

            # Lister les employés trouvés
            for employee in organization_employees:
                print(f"[SiteScheduleBatchEmployeeView][Debug] - Employé à assigner: ID BDD={employee.id}, employee_id={employee.employee_id}, nom={employee.get_full_name()}")

            # Vérifier les employés non trouvés
            found_ids = [emp.id for emp in organization_employees]
            missing_ids = [uid for uid in user_ids if uid not in found_ids]
            if missing_ids:
                print(f"[SiteScheduleBatchEmployeeView][Warning] Employés non trouvés dans l'organisation: {missing_ids}")
                for missing_id in missing_ids:
                    try:
                        user = User.objects.get(id=missing_id)
                        user_orgs = [org.id for org in user.organizations.all()]
                        print(f"[SiteScheduleBatchEmployeeView][Warning] L'employé ID BDD={missing_id}, employee_id={user.employee_id}, nom={user.get_full_name()} existe mais appartient aux organisations: {user_orgs}, pas à {site.organization.id}")
                    except User.DoesNotExist:
                        print(f"[SiteScheduleBatchEmployeeView][Warning] Aucun employé trouvé avec l'ID {missing_id}")

            # Désactiver les assignations qui ne sont plus dans la liste
            # Nous ne désactivons plus les assignations existantes pour permettre à un employé d'être assigné à plusieurs plannings
            # Nous désactivons uniquement les assignations pour ce planning spécifique
            removed = SiteEmployee.objects.filter(
                site=site,
                schedule=schedule
            ).exclude(
                employee_id__in=user_ids
            ).update(is_active=False)
            print(f"[SiteScheduleBatchEmployeeView][Debug] {removed} assignation(s) désactivée(s) pour ce planning")

            # Assigner les employés au planning
            success_count = 0
            error_count = 0
            for employee in organization_employees:
                from sites.serializers import create_or_update_site_employee

                print(f"[SiteScheduleBatchEmployeeView][Debug] Tentative d'assignation pour ID BDD={employee.id}, employee_id={employee.employee_id}, nom={employee.get_full_name()}")
                site_employee, created = create_or_update_site_employee(
                    site=site,
                    employee_id=employee.id,
                    schedule=schedule
                )

                if site_employee:
                    success_count += 1
                    action = "créée" if created else "mise à jour"
                    print(f"[SiteScheduleBatchEmployeeView][Debug] Assignation {action} pour l'employé ID BDD={employee.id}, employee_id={employee.employee_id}, nom={employee.get_full_name()}")
                else:
                    error_count += 1
                    print(f"[SiteScheduleBatchEmployeeView][Error] Erreur lors de l'assignation de l'employé ID BDD={employee.id}, employee_id={employee.employee_id}, nom={employee.get_full_name()}")

            # Vérifier les assignations finales
            final_assignments = SiteEmployee.objects.filter(
                site=site,
                schedule=schedule,
                is_active=True
            )
            print(f"[SiteScheduleBatchEmployeeView][Debug] Nombre d'assignations finales: {final_assignments.count()}")
            for assignment in final_assignments:
                print(f"[SiteScheduleBatchEmployeeView][Debug] - Employé assigné: ID BDD={assignment.employee.id}, employee_id={assignment.employee.employee_id}, nom={assignment.employee.get_full_name()}")

            return Response({
                'message': f'{success_count} employé(s) assigné(s) au planning avec succès, {error_count} échec(s)'
            }, status=201)

        except Site.DoesNotExist as exc:
            print("[SiteScheduleBatchEmployeeView][Error] Site non trouvé")
            raise serializers.ValidationError({
                'site': 'Site non trouvé'
            }) from exc
        except Schedule.DoesNotExist as exc:
            print(f"[SiteScheduleBatchEmployeeView][Error] Planning {schedule_id} non trouvé pour le site {site_id}")
            raise serializers.ValidationError({
                'schedule': 'Planning non trouvé'
            }) from exc
        except Exception as exc:
            print(f"[SiteScheduleBatchEmployeeView][Error] Exception non gérée: {str(exc)}")
            import traceback
            print(f"[SiteScheduleBatchEmployeeView][Error] Traceback: {traceback.format_exc()}")
            raise serializers.ValidationError({
                'error': f'Erreur lors de l\'assignation des employés: {str(exc)}'
            }) from exc


class SitePointagesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TimesheetSerializer

    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        return Timesheet.objects.filter(
            site_id=site_pk
        ).select_related('employee').order_by('-timestamp')


class SiteAnomaliesView(generics.ListAPIView):
    """Vue pour lister les anomalies d'un site"""
    permission_classes = [IsAuthenticated]
    serializer_class = AnomalySerializer

    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        return Anomaly.objects.filter(
            site_id=site_pk
        ).select_related('employee').order_by('-created_at')


class SiteReportsView(generics.ListAPIView):
    """Vue pour lister les rapports d'un site"""
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer

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
            'schedule_employees',
            'schedule_employees__employee'
        )

        if user.is_super_admin:
            return queryset.all()
        elif user.is_admin or user.is_manager:
            return queryset.filter(site__organization__in=user.organizations.all())
        elif user.is_employee:
            return queryset.filter(
                schedule_employees__employee=user,
                schedule_employees__is_active=True
            )
        return Schedule.objects.none()


class SiteAvailableEmployeesView(generics.ListAPIView):
    """Vue pour lister les employés disponibles de l'organisation d'un site"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        try:
            site = Site.objects.get(pk=site_pk)

            # Récupérer les employés de l'organisation qui sont actifs
            return User.objects.filter(
                organizations=site.organization,
                is_active=True,
                role='EMPLOYEE'
            ).order_by('last_name', 'first_name')

        except Site.DoesNotExist:
            return User.objects.none()


class ScheduleStatisticsView(generics.RetrieveAPIView):
    """Vue pour récupérer les statistiques d'un planning"""
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        return Schedule.objects.all()

    def retrieve(self, request, *args, **kwargs):
        schedule = self.get_object()
        statistics = {
            'total_employees': schedule.schedule_employees.filter(is_active=True).count(),
        }
        return Response(statistics)


class ScheduleEmployeesView(generics.ListAPIView):
    """Vue pour lister les employés d'un planning"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        return User.objects.filter(
            employee_sites__schedule=schedule,
            employee_sites__is_active=True
        ).distinct()


class SchedulePointagesView(generics.ListAPIView):
    """Vue pour lister les pointages d'un planning"""
    permission_classes = [IsAuthenticated]
    serializer_class = TimesheetSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        return Timesheet.objects.filter(schedule=schedule).order_by('-created_at')


class ScheduleAnomaliesView(generics.ListAPIView):
    """Vue pour lister les anomalies d'un planning"""
    permission_classes = [IsAuthenticated]
    serializer_class = AnomalySerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        return Anomaly.objects.filter(schedule=schedule).order_by('-created_at')


class ScheduleReportsView(generics.ListAPIView):
    """Vue pour lister les rapports d'un planning"""
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        return Report.objects.filter(schedule=schedule).order_by('-created_at')


class ScheduleUnassignEmployeeView(generics.DestroyAPIView):
    """Vue pour désassigner un employé d'un planning"""
    permission_classes = [IsAuthenticated]

    def get_object(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs['pk'])
        employee = get_object_or_404(User, pk=self.kwargs['employee_pk'])
        return get_object_or_404(
            SiteEmployee,
            schedule=schedule,
            employee=employee,
            is_active=True
        )

    def perform_destroy(self, instance):
        instance.schedule = None
        instance.save()
