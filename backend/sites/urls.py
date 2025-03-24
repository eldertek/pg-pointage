from django.urls import path
from .views import (
    SiteListView, SiteDetailView, ScheduleListView, ScheduleDetailView,
    ScheduleDetailListView, SiteEmployeeListView, SiteEmployeeDetailView,
    ScheduleEmployeeListView, ScheduleEmployeeDetailView
)

urlpatterns = [
    path('', SiteListView.as_view(), name='site-list'),
    path('<int:pk>/', SiteDetailView.as_view(), name='site-detail'),
    path('<int:site_pk>/schedules/', ScheduleListView.as_view(), name='schedule-list'),
    path('<int:site_pk>/schedules/<int:pk>/', ScheduleDetailView.as_view(), name='schedule-detail'),
    path('<int:site_pk>/schedules/<int:schedule_pk>/details/', ScheduleDetailListView.as_view(), name='schedule-detail-list'),
    path('<int:site_pk>/schedules/<int:schedule_pk>/employees/', ScheduleEmployeeListView.as_view(), name='schedule-employee-list'),
    path('<int:site_pk>/schedules/<int:schedule_pk>/employees/<int:pk>/', ScheduleEmployeeDetailView.as_view(), name='schedule-employee-detail'),
    path('<int:site_pk>/employees/', SiteEmployeeListView.as_view(), name='site-employee-list'),
    path('<int:site_pk>/employees/<int:pk>/', SiteEmployeeDetailView.as_view(), name='site-employee-detail'),
]

