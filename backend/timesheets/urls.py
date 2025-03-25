from django.urls import path
from .views import (
    TimesheetListView, TimesheetDetailView, AnomalyListView, 
    AnomalyDetailView, EmployeeReportListView, EmployeeReportDetailView,
    TimesheetCreateView, ReportGenerateView, ScanAnomaliesView
)

urlpatterns = [
    path('', TimesheetListView.as_view(), name='timesheet-list'),
    path('<int:pk>/', TimesheetDetailView.as_view(), name='timesheet-detail'),
    path('create/', TimesheetCreateView.as_view(), name='timesheet-create'),
    path('anomalies/', AnomalyListView.as_view(), name='anomaly-list'),
    path('anomalies/<int:pk>/', AnomalyDetailView.as_view(), name='anomaly-detail'),
    path('scan-anomalies/', ScanAnomaliesView.as_view(), name='scan-anomalies'),
    path('reports/', EmployeeReportListView.as_view(), name='employee-report-list'),
    path('reports/<int:pk>/', EmployeeReportDetailView.as_view(), name='employee-report-detail'),
    path('reports/generate/', ReportGenerateView.as_view(), name='report-generate'),
]

