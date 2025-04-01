from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field
from organizations.models import Organization

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
            
            # Vérifier si les organisations sont actives
            if user.organizations.exists():
                inactive_orgs = user.organizations.filter(is_active=False)
                if inactive_orgs.exists():
                    print("[Auth][Login] Échec: organisations inactives")
                    raise serializers.ValidationError({
                        "error": "Une ou plusieurs organisations auxquelles vous êtes rattaché sont inactives. Veuillez contacter votre administrateur."
                    })
                
        except User.DoesNotExist:
            print("[Auth][Login] Échec: utilisateur non trouvé")
            # On laisse la validation parent gérer ce cas
            pass
            
        return super().validate(attrs)

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs (admin)"""
    password = serializers.CharField(write_only=True, required=False)
    organizations_names = serializers.SerializerMethodField()
    organizations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Organization.objects.all(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'organizations', 'organizations_names', 'phone_number', 
            'is_active', 'employee_id', 'date_joined', 'password',
            'scan_preference', 'simplified_mobile_view'
        )
        read_only_fields = ['date_joined']

    def get_organizations_names(self, obj):
        return [org.name for org in obj.organizations.all()]

    def create(self, validated_data):
        print(f"[DEBUG] UserSerializer.create - validated_data: {validated_data}")
        password = validated_data.pop('password', None)
        organizations = validated_data.pop('organizations', [])
        
        # S'assurer que is_active est True par défaut
        validated_data['is_active'] = validated_data.get('is_active', True)
        user = User.objects.create_user(**validated_data)
        
        # Gérer le mot de passe
        if password:
            user.set_password(password)
        
        # Gérer les organisations
        if organizations:
            print(f"[DEBUG] Ajout des organisations: {organizations}")
            user.organizations.set(organizations)
        
        user.save()
        print(f"[DEBUG] Utilisateur créé: {user.username} (actif: {user.is_active}, orgs: {list(user.organizations.all())})")
        return user

    def update(self, instance, validated_data):
        print(f"[DEBUG] UserSerializer.update - validated_data: {validated_data}")
        password = validated_data.pop('password', None)
        organizations = validated_data.pop('organizations', None)
        
        if password:
            instance.set_password(password)
        
        if organizations is not None:
            print(f"[DEBUG] Mise à jour des organisations: {organizations}")
            instance.organizations.set(organizations)
        
        if 'is_active' in validated_data:
            print(f"[DEBUG] Mise à jour is_active: {instance.is_active} -> {validated_data['is_active']}")
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        print(f"[DEBUG] Utilisateur mis à jour: {instance.username} (orgs: {list(instance.organizations.all())})")
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    organizations_names = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'organizations', 'organizations_names', 'is_active',
            'phone_number', 'employee_id', 'scan_preference', 'simplified_mobile_view'
        ]
        read_only_fields = ['id', 'username', 'email', 'role', 'organizations']
    
    @extend_schema_field({'type': 'array', 'items': {'type': 'string'}})
    def get_organizations_names(self, obj):
        return [org.name for org in obj.organizations.all()]

class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement de nouveaux utilisateurs"""
    password = serializers.CharField(write_only=True)
    organizations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Organization.objects.all(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                 'is_active', 'role', 'organizations', 'phone_number', 
                 'scan_preference', 'simplified_mobile_view']
    
    def create(self, validated_data):
        organizations = validated_data.pop('organizations', [])
        validated_data['is_active'] = True  # Définir is_active à True par défaut
        user = User.objects.create_user(**validated_data)
        
        if organizations:
            print(f"[DEBUG] Ajout des organisations: {organizations}")
            user.organizations.set(organizations)
            
        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['organizations'] = [org.id for org in instance.organizations.all()]
        return ret

