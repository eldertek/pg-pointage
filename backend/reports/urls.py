from django.urls import path
from .views import (
    ReportListView, ReportDetailView, ReportGenerateView,
    ReportDownloadView
)

urlpatterns = [
    path('', ReportListView.as_view(), name='report-list'),
    path('<int:pk>/', ReportDetailView.as_view(), name='report-detail'),
    path('generate/', ReportGenerateView.as_view(), name='report-generate'),
    path('<int:pk>/download/', ReportDownloadView.as_view(), name='report-download'),
]

