from rest_framework import serializers
from .models import Organization
from core.mixins import RolePermissionMixin
from users.models import User

class OrganizationSerializer(serializers.ModelSerializer, RolePermissionMixin):
    """Serializer pour les organisations"""
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'org_id', 'address', 'postal_code', 'city', 'country',
            'phone', 'email', 'contact_email', 'siret', 'logo',
            'notes', 'created_at', 'updated_at', 'is_active', 'users'
        ]
        read_only_fields = ['created_at', 'updated_at', 'org_id']

    def validate(self, data):
        user = self.context['request'].user
        
        # Seuls les super admin peuvent créer/modifier des organisations
        if not user.is_super_admin:
            if self.instance is None:  # Création
                raise serializers.ValidationError("Seul un super admin peut créer une organisation")
            
            # Modification : vérifier si l'utilisateur est admin de cette organisation
            if user.is_admin and not user.organizations.filter(id=self.instance.id).exists():
                raise serializers.ValidationError("Vous n'avez pas les droits pour modifier cette organisation")
            elif not user.is_admin:
                raise serializers.ValidationError("Vous n'avez pas les droits pour modifier une organisation")
        
        return data

    def create(self, validated_data):
        users = validated_data.pop('users', [])
        instance = Organization.objects.create(**validated_data)
        
        # Seul un super admin peut assigner des utilisateurs à la création
        if users and self.context['request'].user.is_super_admin:
            instance.users.set(users)
        
        return instance

    def update(self, instance, validated_data):
        users = validated_data.pop('users', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Gestion des utilisateurs
        if users is not None:
            user = self.context['request'].user
            if user.is_super_admin:
                instance.users.set(users)
            elif user.is_admin and instance in user.organizations.all():
                # Admin peut seulement modifier les utilisateurs de son organisation
                current_users = set(instance.users.values_list('id', flat=True))
                new_users = set(users)
                
                # Ne peut ajouter que des utilisateurs non-admin
                for user_id in new_users - current_users:
                    if User.objects.get(id=user_id).role in [User.Role.SUPER_ADMIN, User.Role.ADMIN]:
                        raise serializers.ValidationError(
                            "Vous ne pouvez pas ajouter d'administrateurs à l'organisation"
                        )
                
                instance.users.set(users)
        
        return instance

