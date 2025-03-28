from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour la connexion avec email"""
    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        print(f"[Auth][Login] Tentative de connexion - email: {attrs.get('email')}")
        try:
            user = User.objects.get(email=attrs.get('email'))
            print(f"[Auth][Login] Utilisateur trouvé: {user.username} (actif: {user.is_active})")
            
            # Vérifier si l'utilisateur est actif
            if not user.is_active:
                print("[Auth][Login] Échec: utilisateur inactif")
                raise serializers.ValidationError({
                    "error": "Ce compte est inactif. Veuillez contacter votre administrateur."
                })
            
            # Vérifier si l'organisation est active (si l'utilisateur appartient à une organisation)
            if user.organization:
                print(f"[Auth][Login] Vérification de l'organisation: {user.organization.name} (active: {user.organization.is_active})")
                if not user.organization.is_active:
                    print("[Auth][Login] Échec: organisation inactive")
                    raise serializers.ValidationError({
                        "error": "L'organisation à laquelle vous êtes rattaché est inactive. Veuillez contacter votre administrateur."
                    })
                
        except User.DoesNotExist:
            print("[Auth][Login] Échec: utilisateur non trouvé")
            # On laisse la validation parent gérer ce cas
            pass
        
        try:
            validated_data = super().validate(attrs)
            print("[Auth][Login] Validation des identifiants réussie")
            return validated_data
        except Exception as e:
            print(f"[Auth][Login] Échec de la validation: {str(e)}")
            raise

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs (admin)"""
    password = serializers.CharField(write_only=True, required=False)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'organization', 'phone_number', 'is_active', 'employee_id', 'date_joined', 'password', 'organization_name', 'scan_preference',
            'simplified_mobile_view'
        )
        read_only_fields = ['date_joined']

    def get_organization_name(self, obj):
        return obj.organization.name if obj.organization else '-'

    def create(self, validated_data):
        print(f"[DEBUG] UserSerializer.create - validated_data: {validated_data}")
        password = validated_data.pop('password', None)
        # S'assurer que is_active est True par défaut
        validated_data['is_active'] = validated_data.get('is_active', True)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        print(f"[DEBUG] Utilisateur créé: {user.username} (actif: {user.is_active})")
        return user

    def update(self, instance, validated_data):
        print(f"[DEBUG] UserSerializer.update - validated_data: {validated_data}")
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        if 'is_active' in validated_data:
            print(f"[DEBUG] Mise à jour is_active: {instance.is_active} -> {validated_data['is_active']}")
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    organization_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'organization', 'organization_name', 'is_active',
            'phone_number', 'employee_id', 'scan_preference', 'simplified_mobile_view'
        ]
        read_only_fields = ['id', 'username', 'email', 'role', 'organization']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_organization_name(self, obj) -> str:
        return obj.organization.name if obj.organization else ''

class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement de nouveaux utilisateurs"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'is_active', 'role']
    
    def create(self, validated_data):
        validated_data['is_active'] = True  # Définir is_active à True par défaut
        user = User.objects.create_user(**validated_data)
        return user

