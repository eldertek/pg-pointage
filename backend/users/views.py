from rest_framework import status, generics, permissions, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model, logout
from django.utils import timezone
from datetime import timedelta
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegisterSerializer,
    CustomTokenObtainPairSerializer
)
from .models import User
from drf_spectacular.utils import extend_schema, OpenApiResponse
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule
from reports.models import Report
from sites.serializers import SiteSerializer, ScheduleSerializer
from reports.serializers import ReportSerializer

User = get_user_model()

class UserLoginView(TokenObtainPairView):
    """Vue pour la connexion des utilisateurs et l'obtention des tokens JWT"""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print(f"[DEBUG] Tentative de connexion - données reçues: {request.data}")
        try:
            response = super().post(request, *args, **kwargs)
            print(f"[DEBUG] Connexion réussie - status: {response.status_code}")
            return response
        except Exception as e:
            print(f"[DEBUG] Échec de connexion - erreur: {str(e)}")
            raise

class UserLogoutSerializer(serializers.Serializer):
    """Serializer pour la déconnexion"""
    pass

class UserChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

class UserLogoutView(generics.GenericAPIView):
    """Vue pour la déconnexion"""
    serializer_class = UserLogoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(description='Déconnexion réussie'),
        }
    )
    def post(self, request):
        logout(request)
        return Response({'detail': 'Déconnexion réussie'})

class UserRegistrationView(generics.CreateAPIView):
    """Vue pour l'enregistrement de nouveaux utilisateurs"""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print(f"[Users][Register] Données reçues: {request.data}")
        response = super().create(request, *args, **kwargs)
        print(f"[Users][Register] Utilisateur créé avec succès: {response.data}")
        return response

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour obtenir et mettre à jour le profil de l'utilisateur connecté"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    """Vue pour lister les utilisateurs"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
            
        user = self.request.user
        print(f"[Users][Auth] Utilisateur connecté: {user.username} (role: {user.role})")
        print(f"[Users][Auth] Droits: is_super_admin={user.is_super_admin}, is_admin={user.is_admin}, is_manager={user.is_manager}")
        
        queryset = User.objects.all()
        
        # Super Admin voit tout
        if user.is_super_admin:
            pass
        # Admin et Manager voient les utilisateurs de leurs organisations
        elif user.is_admin or user.is_manager:
            organizations = user.organizations.all()
            queryset = queryset.filter(organizations__in=organizations)
        # Employé ne voit que son profil
        else:
            queryset = queryset.filter(id=user.id)
        
        print(f"[Users][Count] Nombre total d'utilisateurs: {queryset.count()}")
        print(f"[Users][Debug] Paramètres de la requête: {self.request.query_params}")
        
        # Filtrer par rôle si spécifié
        role = self.request.query_params.get('role')
        if role:
            print(f"[Users][Filter] Filtrage par rôle: {role}")
            queryset = queryset.filter(role=role)
            print(f"[Users][Count] Après filtre rôle ({role}): {queryset.count()}")
            print(f"[Users][Debug] Utilisateurs trouvés avec le rôle {role}:", [
                f"{u.username} (role: {u.role})" 
                for u in queryset
            ])
        
        # Filtrer par organisation si spécifié
        organization = self.request.query_params.get('organization')
        if organization:
            print(f"[Users][Filter] Filtrage par organisation: {organization}")
            queryset = queryset.filter(organizations=organization)
            print(f"[Users][Count] Après filtre organisation ({organization}): {queryset.count()}")
            print(f"[Users][Debug] Utilisateurs trouvés dans l'organisation {organization}:", [
                f"{u.username} (role: {u.role})" 
                for u in queryset
            ])
        
        return queryset.distinct()

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un utilisateur spécifique (admin seulement)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def partial_update(self, request, *args, **kwargs):
        print(f"[DEBUG] Requête PATCH reçue - data: {request.data}")
        instance = self.get_object()
        print(f"[DEBUG] Utilisateur trouvé: {instance.username} (id: {instance.id})")
        
        # Permettre explicitement la modification de is_active
        if 'is_active' in request.data:
            old_status = instance.is_active
            instance.is_active = request.data['is_active']
            instance.save()
            print(f"[DEBUG] Statut modifié: {old_status} -> {instance.is_active}")
            
        response = super().partial_update(request, *args, **kwargs)
        print(f"[DEBUG] Réponse: {response.status_code}")
        return response

class UserChangePasswordView(generics.GenericAPIView):
    """Vue pour changer le mot de passe"""
    serializer_class = UserChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=UserChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description='Mot de passe changé avec succès'),
            400: OpenApiResponse(description='Données invalides')
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Vérifier l'ancien mot de passe
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['Mot de passe incorrect']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que les nouveaux mots de passe correspondent
        if serializer.validated_data['new_password'] != serializer.validated_data['confirm_password']:
            return Response(
                {'confirm_password': ['Les mots de passe ne correspondent pas']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Changer le mot de passe
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'detail': 'Mot de passe changé avec succès'})

class UserStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            
            # Calculer la période (30 derniers jours)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            # Récupérer les pointages
            timesheets = Timesheet.objects.filter(
                employee=user,
                timestamp__range=[start_date, end_date]
            ).order_by('timestamp')
            
            # Calculer le total des heures
            total_hours = 0
            entry_time = None
            
            for timesheet in timesheets:
                if timesheet.entry_type == 'IN':
                    entry_time = timesheet.timestamp
                elif timesheet.entry_type == 'OUT' and entry_time:
                    duration = timesheet.timestamp - entry_time
                    total_hours += duration.total_seconds() / 3600  # Convertir en heures
                    entry_time = None
            
            # Compter les anomalies
            anomalies_count = Anomaly.objects.filter(
                timesheet__employee=user,
                timesheet__timestamp__range=[start_date, end_date]
            ).count()
            
            return Response({
                'total_hours': round(total_hours, 2),
                'anomalies': anomalies_count,
                'period': {
                    'start': start_date.date(),
                    'end': end_date.date()
                }
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserSitesView(generics.ListAPIView):
    """Vue pour lister les sites d'un utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        # Sites où l'utilisateur est employé
        employee_sites = Site.objects.filter(employees__employee=user, employees__is_active=True)
        # Sites où l'utilisateur est manager
        manager_sites = Site.objects.filter(manager=user)
        # Sites où l'utilisateur a des plannings assignés
        scheduled_sites = Site.objects.filter(
            schedules__assigned_employees__employee=user,
            schedules__assigned_employees__is_active=True
        )
        
        # Combiner tous les sites uniques
        return (employee_sites | manager_sites | scheduled_sites).distinct()
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = SiteSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = SiteSerializer(queryset, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

class UserSchedulesView(generics.ListAPIView):
    """Vue pour lister les plannings d'un utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        return Schedule.objects.filter(
            assigned_employees__employee=user,
            assigned_employees__is_active=True
        ).distinct()
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ScheduleSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = ScheduleSerializer(queryset, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

class UserReportsView(generics.ListAPIView):
    """Vue pour lister les rapports d'un utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        return Report.objects.filter(created_by=user)
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ReportSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = ReportSerializer(queryset, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

