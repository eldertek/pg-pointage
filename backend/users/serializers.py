from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs (admin)"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                'organization', 'phone_number', 'is_active', 'employee_id', 'date_joined']
        read_only_fields = ['date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur (utilisateur connecté)"""
    organization_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                'organization', 'organization_name', 'phone_number', 'employee_id']
        read_only_fields = ['id', 'role', 'organization', 'organization_name', 'employee_id']
    
    def get_organization_name(self, obj):
        return obj.organization.name if obj.organization else None

class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement de nouveaux utilisateurs"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

