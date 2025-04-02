""" URLs pour les sites """
from django.urls import path
from .views import (
    SiteListView, SiteDetailView, SiteEmployeesView, SiteStatisticsView,
    SiteSchedulesView, SiteScheduleDetailView, SiteScheduleDetailListView,
    SiteScheduleBatchEmployeeView, AllSchedulesView, SitePointagesView,
    SiteAnomaliesView, SiteReportsView, SiteAvailableEmployeesView,
    ScheduleStatisticsView, ScheduleEmployeesView, SchedulePointagesView,
    ScheduleAnomaliesView, ScheduleReportsView, ScheduleUnassignEmployeeView
)

urlpatterns = [
    # Sites
    path('', SiteListView.as_view(), name='site-list'),
    path('<int:pk>/', SiteDetailView.as_view(), name='site-detail'),
    path('<int:pk>/statistics/', SiteStatisticsView.as_view(),
         name='site-statistics'),
    path('<int:pk>/employees/', SiteEmployeesView.as_view(), name='site-employees'),
    path('<int:pk>/available-employees/',
         SiteAvailableEmployeesView.as_view(), name='site-available-employees'),
    path('<int:pk>/pointages/', SitePointagesView.as_view(), name='site-pointages'),
    path('<int:pk>/anomalies/', SiteAnomaliesView.as_view(), name='site-anomalies'),
    path('<int:pk>/reports/', SiteReportsView.as_view(), name='site-reports'),

    # Plannings par site
    path('<int:pk>/schedules/', SiteSchedulesView.as_view(), name='site-schedules'),
    path('<int:pk>/schedules/<int:schedule_pk>/',
         SiteScheduleDetailView.as_view(), name='site-schedule-detail'),
    path('<int:pk>/schedules/<int:schedule_pk>/details/',
         SiteScheduleDetailListView.as_view(), name='site-schedule-detail-list'),
    path('<int:pk>/schedules/<int:schedule_pk>/employees/batch/',
         SiteScheduleBatchEmployeeView.as_view(), name='site-schedule-batch-employees'),

    # Plannings (endpoints directs)
    path('schedules/', AllSchedulesView.as_view(), name='all-schedules'),
    path('schedules/<int:pk>/', SiteScheduleDetailView.as_view(),
         name='schedule-detail'),
    path('schedules/<int:pk>/statistics/',
         ScheduleStatisticsView.as_view(), name='schedule-statistics'),
    path('schedules/<int:pk>/employees/',
         ScheduleEmployeesView.as_view(), name='schedule-employees'),
    path('schedules/<int:pk>/employees/<int:employee_pk>/',
         ScheduleUnassignEmployeeView.as_view(), name='schedule-unassign-employee'),
    path('schedules/<int:pk>/pointages/',
         SchedulePointagesView.as_view(), name='schedule-pointages'),
    path('schedules/<int:pk>/anomalies/',
         ScheduleAnomaliesView.as_view(), name='schedule-anomalies'),
    path('schedules/<int:pk>/reports/',
         ScheduleReportsView.as_view(), name='schedule-reports'),
]
