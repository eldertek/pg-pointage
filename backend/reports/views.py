from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
import os
from .models import Report
from .serializers import ReportSerializer, ReportGenerateSerializer
from sites.permissions import IsSiteOrganizationManager
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

class ReportListView(generics.ListCreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Report.objects.all()
        
        # Filtres
        search = self.request.query_params.get('search', '')
        report_type = self.request.query_params.get('type', '')
        report_format = self.request.query_params.get('format', '')
        site_id = self.request.query_params.get('site', None)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        if report_format:
            queryset = queryset.filter(report_format=report_format)
        if site_id:
            queryset = queryset.filter(site_id=site_id)
            
        return queryset.select_related('site')

class ReportDetailView(generics.RetrieveAPIView):
    """Vue pour obtenir les détails d'un rapport"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Report.objects.all()
        elif user.is_admin or user.is_manager:
            return Report.objects.filter(organization__in=user.organizations.all())
        else:
            return Report.objects.filter(created_by=user)

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
        
        try:
            print(f"[Reports][Generate] Début de la génération du rapport - Données reçues: {request.data}")
            
            # Récupérer l'organisation de l'utilisateur
            if request.user.is_super_admin:
                print(f"[Reports][Generate] Utilisateur super admin: {request.user.email}")
                # Pour le super admin, si site est null, on génère un rapport pour tous les sites de toutes les organisations
                site_id = serializer.validated_data.get('site')
                if site_id:
                    print(f"[Reports][Generate] Site spécifié: {site_id}")
                    # Si un site est spécifié, utiliser son organisation
                    from sites.models import Site
                    site = Site.objects.get(id=site_id)
                    organization = site.organization
                    print(f"[Reports][Generate] Organisation du site: {organization.name}")
                else:
                    print("[Reports][Generate] Aucun site spécifié - Rapport pour tous les sites")
                    # Si site est null, on utilise None pour l'organisation
                    # Cela indiquera que le rapport doit inclure tous les sites de toutes les organisations
                    organization = None
            else:
                print(f"[Reports][Generate] Utilisateur non super admin: {request.user.email}")
                # Pour les autres utilisateurs, utiliser leur première organisation
                organizations = request.user.organizations.all()
                if not organizations.exists():
                    print("[Reports][Generate] Erreur: Utilisateur non associé à une organisation")
                    raise serializers.ValidationError({
                        'error': 'Utilisateur non associé à une organisation'
                    })
                organization = organizations.first()
                print(f"[Reports][Generate] Organisation de l'utilisateur: {organization.name}")
            
            print("[Reports][Generate] Création du rapport...")
            report = Report.objects.create(
                name=serializer.validated_data['name'],
                report_type=serializer.validated_data['report_type'],
                report_format=serializer.validated_data['report_format'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                site_id=serializer.validated_data.get('site'),  # Sera None pour tous les sites
                organization=organization,  # Peut être None pour le super admin si tous les sites
                created_by=request.user
            )
            print(f"[Reports][Generate] Rapport créé avec succès - ID: {report.id}")
            
            return Response({
                'id': report.id,
                'message': 'Rapport en cours de génération'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"[Reports][Generate] Erreur lors de la génération du rapport: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ReportDownloadView(generics.RetrieveAPIView):
    queryset = Report.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        report = self.get_object()
        if not report.file:
            return Response(
                {'error': 'Le fichier n\'est pas encore disponible'},
                status=status.HTTP_404_NOT_FOUND
            )

        file_path = report.file.path
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        
        return Response(
            {'error': 'Fichier non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )

class ReportDeleteView(generics.DestroyAPIView):
    """Vue pour supprimer un rapport"""
    queryset = Report.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Report.objects.all()
        elif user.is_admin or user.is_manager:
            return Report.objects.filter(organization__in=user.organizations.all())
        else:
            return Report.objects.filter(created_by=user)
            
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # Supprimer le fichier physique s'il existe
            if instance.file and os.path.exists(instance.file.path):
                os.remove(instance.file.path)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

