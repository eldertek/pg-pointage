from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
from .models import Report
from .serializers import ReportSerializer
from sites.permissions import IsSiteOrganizationManager

class ReportListView(generics.ListAPIView):
    """Vue pour lister les rapports"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Report.objects.all()
        elif user.is_manager and user.organization:
            return Report.objects.filter(organization=user.organization)
        return Report.objects.none()

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

class ReportGenerateView(APIView):
    """Vue pour générer un rapport"""
    permission_classes = [permissions.IsAuthenticated, IsSiteOrganizationManager]
    
    def post(self, request):
        # Logique de génération de rapport
        # À implémenter en fonction des besoins
        
        return Response({"message": "Génération de rapport lancée"}, status=status.HTTP_202_ACCEPTED)

class ReportDownloadView(APIView):
    """Vue pour télécharger un rapport"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
            
            # Vérifier les permissions
            user = request.user
            if not user.is_super_admin and (not user.is_manager or user.organization != report.organization):
                return Response({"detail": "Vous n'avez pas la permission de télécharger ce rapport."}, 
                                status=status.HTTP_403_FORBIDDEN)
            
            # Retourner le fichier
            return FileResponse(open(report.file.path, 'rb'), as_attachment=True, filename=report.file.name.split('/')[-1])
        except Report.DoesNotExist:
            return Response({"detail": "Rapport introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

