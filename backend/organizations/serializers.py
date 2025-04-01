from rest_framework import serializers
from .models import Organization

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer pour les organisations"""
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'org_id', 'address', 'postal_code', 'city', 'country',
            'phone', 'email', 'contact_email', 'siret', 'logo',
            'notes', 'created_at', 'updated_at', 'is_active', 'users'
        ]
        read_only_fields = ['created_at', 'updated_at', 'org_id']

    def create(self, validated_data):
        users = validated_data.pop('users', [])
        instance = Organization.objects.create(**validated_data)
        if users:
            instance.users.set(users)
        return instance

    def update(self, instance, validated_data):
        users = validated_data.pop('users', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if users is not None:
            instance.users.set(users)
        return instance

