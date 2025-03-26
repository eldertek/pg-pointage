from django.urls import path
from .views import (
    SiteListView, SiteDetailView, ScheduleListView, ScheduleDetailView,
    ScheduleDetailListView, SiteEmployeeListView, SiteEmployeeDetailView,
    GlobalScheduleListView, GlobalScheduleDetailView
)

urlpatterns = [
    path('', SiteListView.as_view(), name='site-list'),
    path('<int:pk>/', SiteDetailView.as_view(), name='site-detail'),
    path('schedules/', GlobalScheduleListView.as_view(), name='global-schedule-list'),
    path('schedules/<int:pk>/', GlobalScheduleDetailView.as_view(), name='global-schedule-detail'),
    path('<int:site_pk>/schedules/', ScheduleListView.as_view(), name='schedule-list'),
    path('<int:site_pk>/schedules/<int:pk>/', ScheduleDetailView.as_view(), name='schedule-detail'),
    path('<int:site_pk>/schedules/<int:schedule_pk>/details/', ScheduleDetailListView.as_view(), name='schedule-detail-list'),
    path('<int:site_pk>/employees/', SiteEmployeeListView.as_view(), name='site-employee-list'),
    path('<int:site_pk>/employees/<int:pk>/', SiteEmployeeDetailView.as_view(), name='site-employee-detail'),
]

