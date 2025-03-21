from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from .models import Timesheet, Anomaly, EmployeeReport
from .serializers import (
    TimesheetSerializer, TimesheetCreateSerializer,
    AnomalySerializer, EmployeeReportSerializer
)
from sites.permissions import IsSiteOrganizationManager

class TimesheetListView(generics.ListAPIView):
    """Vue pour lister les pointages"""
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Timesheet.objects.all()
        elif user.is_manager and user.organization:
            return Timesheet.objects.filter(site__organization=user.organization)
        else:
            return Timesheet.objects.filter(employee=user)

class TimesheetDetailView(generics.RetrieveAPIView):
    """Vue pour obtenir les détails d'un pointage"""
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Timesheet.objects.all()
        elif user.is_manager and user.organization:
            return Timesheet.objects.filter(site__organization=user.organization)
        else:
            return Timesheet.objects.filter(employee=user)

class TimesheetCreateView(generics.CreateAPIView):
    """Vue pour créer un pointage via l'application mobile"""
    serializer_class = TimesheetCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

class AnomalyListView(generics.ListCreateAPIView):
    """Vue pour lister les anomalies et en créer de nouvelles"""
    serializer_class = AnomalySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Anomaly.objects.all()
        elif user.is_manager and user.organization:
            return Anomaly.objects.filter(site__organization=user.organization)
        else:
            return Anomaly.objects.filter(employee=user)

class AnomalyDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour obtenir et mettre à jour une anomalie"""
    serializer_class = AnomalySerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Anomaly.objects.all()
        elif user.is_manager and user.organization:
            return Anomaly.objects.filter(site__organization=user.organization)
        else:
            return Anomaly.objects.filter(employee=user)
    
    def perform_update(self, serializer):
        if self.request.user.is_manager or self.request.user.is_super_admin:
            # Enregistrer qui a corrigé l'anomalie
            serializer.save(
                corrected_by=self.request.user,
                correction_date=timezone.now()
            )
        else:
            serializer.save()

class EmployeeReportListView(generics.ListAPIView):
    """Vue pour lister les rapports d'employés"""
    serializer_class = EmployeeReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return EmployeeReport.objects.all()
        elif user.is_manager and user.organization:
            return EmployeeReport.objects.filter(site__organization=user.organization)
        else:
            return EmployeeReport.objects.filter(employee=user)

class EmployeeReportDetailView(generics.RetrieveAPIView):
    """Vue pour obtenir les détails d'un rapport d'employé"""
    serializer_class = EmployeeReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return EmployeeReport.objects.all()
        elif user.is_manager and user.organization:
            return EmployeeReport.objects.filter(site__organization=user.organization)
        else:
            return EmployeeReport.objects.filter(employee=user)

class ReportGenerateView(APIView):
    """Vue pour générer un rapport"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Logique de génération de rapport
        # À implémenter en fonction des besoins
        return Response({"message": "Génération de rapport lancée"}, status=status.HTTP_202_ACCEPTED)

