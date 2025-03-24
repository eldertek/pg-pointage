from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('stats/', views.get_dashboard_stats, name='stats'),
    path('anomalies/recent/', views.get_recent_anomalies, name='recent_anomalies'),
] 