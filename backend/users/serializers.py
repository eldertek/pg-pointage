""" Serializers pour les utilisateurs """
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field
from organizations.models import Organization
from core.mixins import OrganizationPermissionMixin, RolePermissionMixin
from .models import User

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour la connexion avec email"""
    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        print(
            f"[Auth][Login] Tentative de connexion - email: {attrs.get('email')}")
        try:
            user = User.objects.get(email=attrs.get('email'))
            print(
                f"[Auth][Login] Utilisateur trouvé: {user.username} (actif: {user.is_active})")

            # Vérifier si l'utilisateur est actif
            if not user.is_currently_active:
                print("[Auth][Login] Échec: utilisateur inactif")
                raise serializers.ValidationError({
                    "error": "Ce compte est inactif. Veuillez contacter votre administrateur."
                })

            # Vérifier si les organisations sont actives
            if user.organizations.exists():
                from core.utils import is_entity_active
                inactive_orgs = [org for org in user.organizations.all() if not is_entity_active(org)]
                if inactive_orgs:
                    print("[Auth][Login] Échec: organisations inactives")
                    raise serializers.ValidationError({
                        "error": "Une ou plusieurs organisations auxquelles vous êtes rattaché sont inactives. Veuillez contacter votre administrateur."
                    })

        except User.DoesNotExist:
            print("[Auth][Login] Échec: utilisateur non trouvé")
            # On laisse la validation parent gérer ce cas
            pass

        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer, OrganizationPermissionMixin, RolePermissionMixin):
    """Serializer pour les utilisateurs (admin)"""
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    reset_password = serializers.BooleanField(write_only=True, required=False)
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
            'is_active', 'activation_start_date', 'activation_end_date', 'employee_id', 'date_joined', 'password',
            'scan_preference', 'simplified_mobile_view', 'language', 'reset_password'
        )
        read_only_fields = ['date_joined', 'employee_id']

    def get_organizations_names(self, obj):
        return [org.name for org in obj.organizations.all()]

    def to_representation(self, instance):
        # Filtrer les utilisateurs en fonction du rôle de l'utilisateur connecté
        user = self.context['request'].user
        data = super().to_representation(instance)

        # Si l'utilisateur est un manager, il ne doit voir que les employés
        if user.role == User.Role.MANAGER and instance.role != User.Role.EMPLOYEE:
            return None

        # Si l'utilisateur est un admin, il ne doit pas voir les super admin
        if user.role == User.Role.ADMIN and instance.role == User.Role.SUPER_ADMIN:
            return None

        # S'assurer que les IDs des organisations sont correctement renvoyés
        data['organizations'] = [org.id for org in instance.organizations.all()]

        print(f"[UserSerializer][to_representation] Organisations pour {instance.username}: {data['organizations']}")

        return data

    def to_internal_value(self, data):
        # Convertir les chaînes vides des dates d'activation en None pour éviter les erreurs de format
        for date_field in ['activation_start_date', 'activation_end_date']:
            if date_field in data and data.get(date_field) == '':
                data.pop(date_field)
        return super().to_internal_value(data)

    def validate(self, data):
        user = self.context['request'].user

        # Validation du rôle
        if 'role' in data:
            # Seuls les super admin et admin peuvent changer les rôles
            if not user.is_super_admin and not user.is_admin:
                raise serializers.ValidationError({
                    "role": "Vous n'avez pas les droits pour modifier le rôle"
                })

            # Les admins ne peuvent pas créer de super admin
            if data['role'] == User.Role.SUPER_ADMIN and not user.is_super_admin:
                raise serializers.ValidationError({
                    "role": "Seul un super admin peut créer d'autres super admin"
                })

        # Validation des organisations
        if 'organizations' in data:
            if user.is_super_admin:
                return data
            elif user.is_admin:
                # Vérifier que les organisations sont celles de l'admin
                if not all(org.id in user.organizations.values_list('id', flat=True)
                           for org in data['organizations']):
                    raise serializers.ValidationError({
                        "organizations": "Vous ne pouvez pas assigner des organisations auxquelles vous n'appartenez pas"
                    })
            else:
                raise serializers.ValidationError({
                    "organizations": "Vous n'avez pas les droits pour modifier les organisations"
                })

        return data

    def create(self, validated_data):
        # Vérifier les permissions selon le rôle de l'utilisateur connecté
        user = self.context['request'].user
        if not user.is_super_admin and not user.is_admin:
            raise serializers.ValidationError(
                "Vous n'avez pas les droits pour créer un utilisateur")

        password = validated_data.pop('password', None)
        organizations = validated_data.pop('organizations', [])

        # S'assurer que is_active est True par défaut
        validated_data['is_active'] = validated_data.get('is_active', True)
        user = User.objects.create_user(**validated_data)

        if password:
            user.set_password(password)

        if organizations:
            # Vérifier les permissions sur les organisations
            for org in organizations:
                self.validate_organization(org.id)
            user.organizations.set(organizations)

        user.save()
        return user

    def update(self, instance, validated_data):
        # Vérifier les permissions selon le rôle
        user = self.context['request'].user
        if not user.is_super_admin:
            if user.is_admin:
                # Admin ne peut modifier que les utilisateurs de ses organisations
                if not instance.organizations.filter(id__in=user.organizations.values_list('id', flat=True)).exists():
                    raise serializers.ValidationError(
                        "Vous ne pouvez pas modifier cet utilisateur")
            elif user.is_manager:
                # Manager ne peut modifier que les employés de ses sites
                if instance.role != User.Role.EMPLOYEE or not instance.organizations.filter(id__in=user.organizations.values_list('id', flat=True)).exists():
                    raise serializers.ValidationError(
                        "Vous ne pouvez pas modifier cet utilisateur")
            else:
                # Les autres ne peuvent modifier que leur propre profil
                if instance.id != user.id:
                    raise serializers.ValidationError(
                        "Vous ne pouvez pas modifier cet utilisateur")

        password = validated_data.pop('password', None)
        reset_password = validated_data.pop('reset_password', False)
        organizations = validated_data.pop('organizations', None)

        if reset_password:
            if not (user.is_super_admin or (user.is_admin and instance.organizations.filter(id__in=user.organizations.values_list('id', flat=True)).exists())):
                raise serializers.ValidationError(
                    "Vous n'avez pas les droits pour réinitialiser le mot de passe de cet utilisateur")
            # Générer un mot de passe aléatoire
            from django.utils.crypto import get_random_string
            password = get_random_string(12)
            instance.set_password(password)
            # Envoyer un email avec le nouveau mot de passe
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                'Réinitialisation de votre mot de passe',
                f'Votre nouveau mot de passe est : {password}\n\nVeuillez le changer à votre prochaine connexion.',
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
                fail_silently=False,
            )
        elif password:
            instance.set_password(password)

        if organizations is not None:
            # Vérifier les permissions sur les organisations
            for org in organizations:
                self.validate_organization(org.id)
            instance.organizations.set(organizations)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    organizations_names = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        # Convertir les chaînes vides des dates d'activation en None
        for date_field in ['activation_start_date', 'activation_end_date']:
            if date_field in data and data.get(date_field) == '':
                data.pop(date_field)
        return super().to_internal_value(data)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'organizations', 'organizations_names', 'is_active',
            'activation_start_date', 'activation_end_date', 'phone_number', 'employee_id',
            'scan_preference', 'simplified_mobile_view', 'language'
        ]
        read_only_fields = ['id', 'username', 'email', 'role', 'organizations', 'employee_id']

    @extend_schema_field({'type': 'array', 'items': {'type': 'string'}})
    def get_organizations_names(self, obj):
        return [org.name for org in obj.organizations.all()]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement de nouveaux utilisateurs"""
    password = serializers.CharField(write_only=True)
    organizations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Organization.objects.all(),
        required=False,
        allow_empty=True
    )

    def to_internal_value(self, data):
        # Convertir les chaînes vides des dates d'activation en None
        for date_field in ['activation_start_date', 'activation_end_date']:
            if date_field in data and data.get(date_field) == '':
                data.pop(date_field)
        return super().to_internal_value(data)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                  'is_active', 'activation_start_date', 'activation_end_date', 'role', 'organizations', 'phone_number',
                  'scan_preference', 'simplified_mobile_view', 'language', 'employee_id']
        read_only_fields = ['employee_id']

    def validate(self, data):
        user = self.context['request'].user

        # Validation du rôle
        if 'role' in data:
            # Les admins ne peuvent pas créer de super admin
            if data['role'] == User.Role.SUPER_ADMIN and not user.is_super_admin:
                raise serializers.ValidationError({
                    "role": "Seul un super admin peut créer d'autres super admin"
                })

        # Validation des organisations
        if 'organizations' in data:
            if user.is_super_admin:
                return data
            elif user.is_admin:
                # Vérifier que les organisations sont celles de l'admin
                if not all(org.id in user.organizations.values_list('id', flat=True)
                           for org in data['organizations']):
                    raise serializers.ValidationError({
                        "organizations": "Vous ne pouvez pas assigner des organisations auxquelles vous n'appartenez pas"
                    })

        return data

    def create(self, validated_data):
        organizations = validated_data.pop('organizations', [])
        # Définir is_active à True par défaut
        validated_data['is_active'] = True
        user = User.objects.create_user(**validated_data)

        if organizations:
            print(f"[DEBUG] Ajout des organisations: {organizations}")
            user.organizations.set(organizations)
            user.save()  # Sauvegarder après l'ajout des organisations

        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['organizations'] = [org.id for org in instance.organizations.all()]
        return ret
