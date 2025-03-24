from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegisterSerializer,
    CustomTokenObtainPairSerializer
)

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

class UserLogoutView(APIView):
    """Vue pour la déconnexion des utilisateurs"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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

class UserListView(generics.ListCreateAPIView):
    """Vue pour lister tous les utilisateurs et en créer de nouveaux"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        role_filter = self.request.query_params.get('role')
        
        queryset = User.objects.all()
        
        # Filtrer par rôle si spécifié
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        # Super admin voit tous les utilisateurs
        if user.is_super_admin:
            return queryset
        # Manager voit les utilisateurs de son organisation
        elif user.is_manager and user.organization:
            return queryset.filter(organization=user.organization)
        # Les employés ne voient personne
        return User.objects.none()
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

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

