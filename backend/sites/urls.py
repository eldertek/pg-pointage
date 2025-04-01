from django.urls import path
from .views import (
    SiteListView, SiteDetailView, SiteEmployeesView, SiteSchedulesView,
    SitePointagesView, SiteAnomaliesView, SiteReportsView, SiteStatisticsView,
    SiteScheduleDetailView, SiteScheduleDetailListView, SiteScheduleBatchEmployeeView,
    AllSchedulesView
)

urlpatterns = [
    # Routes principales des sites
    path('', SiteListView.as_view(), name='site-list'),
    path('<int:pk>/', SiteDetailView.as_view(), name='site-detail'),
    path('<int:pk>/statistics/', SiteStatisticsView.as_view(), name='site-statistics'),
    
    # Routes des employés
    path('<int:pk>/employees/', SiteEmployeesView.as_view(), name='site-employees'),
    
    # Routes des plannings
    path('schedules/', AllSchedulesView.as_view(), name='all-schedules'),
    path('<int:pk>/schedules/', SiteSchedulesView.as_view(), name='site-schedules'),
    path('<int:pk>/schedules/<int:schedule_pk>/', SiteScheduleDetailView.as_view(), name='site-schedule-detail'),
    path('<int:pk>/schedules/<int:schedule_pk>/details/', SiteScheduleDetailListView.as_view(), name='site-schedule-detail-list'),
    path('<int:pk>/schedules/<int:schedule_pk>/employees/batch/', SiteScheduleBatchEmployeeView.as_view(), name='site-schedule-batch-employees'),
    
    # Routes des pointages et anomalies
    path('<int:pk>/pointages/', SitePointagesView.as_view(), name='site-pointages'),
    path('<int:pk>/anomalies/', SiteAnomaliesView.as_view(), name='site-anomalies'),
    path('<int:pk>/reports/', SiteReportsView.as_view(), name='site-reports'),
]

