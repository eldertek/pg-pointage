from rest_framework import status, generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, logout
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegisterSerializer,
    CustomTokenObtainPairSerializer
)
from .models import User
from sites.permissions import IsSiteOrganizationManager
from drf_spectacular.utils import extend_schema, OpenApiResponse

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
        if user.is_super_admin:
            return User.objects.all()
        elif user.is_manager and user.organization:
            return User.objects.filter(organization=user.organization)
        return User.objects.none()

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

