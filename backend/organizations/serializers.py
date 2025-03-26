from rest_framework import serializers
from .models import Organization

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer pour les organisations"""
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'org_id', 'address', 'postal_code', 'city', 'country',
            'phone', 'email', 'contact_email', 'siret', 'logo',
            'notes', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['created_at', 'updated_at', 'org_id']

    def create(self, validated_data):
        # Créer l'organisation sans org_id (il sera généré automatiquement par le modèle)
        instance = Organization.objects.create(**validated_data)
        return instance

