from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
from .models import Report
from .serializers import ReportSerializer
from sites.permissions import IsSiteOrganizationManager
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

class ReportListView(generics.ListCreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Report.objects.none()
            
        user = self.request.user
        if user.is_super_admin:
            return Report.objects.all()
        elif user.is_manager and user.organization:
            return Report.objects.filter(organization=user.organization)
        else:
            return Report.objects.filter(created_by=user)

class ReportDetailView(generics.RetrieveAPIView):
    """Vue pour obtenir les détails d'un rapport"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Report.objects.all()
        elif user.is_manager and user.organization:
            return Report.objects.filter(organization=user.organization)
        return Report.objects.none()

class ReportGenerateSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=Report.ReportType.choices)
    report_format = serializers.ChoiceField(choices=Report.ReportFormat.choices)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    site = serializers.IntegerField(required=False)

class ReportGenerateView(generics.CreateAPIView):
    serializer_class = ReportGenerateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=ReportGenerateSerializer,
        responses={
            201: OpenApiResponse(description='Rapport généré avec succès'),
            400: OpenApiResponse(description='Données invalides')
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Logique de génération du rapport...
        return Response({'message': 'Rapport en cours de génération'}, status=status.HTTP_201_CREATED)

class ReportDownloadView(generics.RetrieveAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all()
    
    @extend_schema(
        responses={
            200: OpenApiResponse(description='Fichier du rapport'),
            404: OpenApiResponse(description='Rapport non trouvé')
        }
    )
    def get(self, request, *args, **kwargs):
        report = self.get_object()
        if not report.file:
            return Response(
                {'error': 'Le fichier n\'est pas encore disponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Logique pour servir le fichier...
        return Response({'file_url': report.file.url})

