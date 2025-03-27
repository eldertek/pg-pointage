from django.urls import path
from .views import DashboardView, RecentAnomaliesView

app_name = 'dashboard'

urlpatterns = [
    path('stats/', DashboardView.as_view(), name='dashboard-stats'),
    path('anomalies/recent/', RecentAnomaliesView.as_view(), name='recent-anomalies'),
] 