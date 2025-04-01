from django.urls import path
from .views import (
    OrganizationListView, OrganizationDetailView,
    OrganizationUsersView, OrganizationStatisticsView,
    OrganizationUnassignedEmployeesView, OrganizationUnassignedSitesView,
    OrganizationSitesView, assign_site_to_organization,
    OrganizationTimesheetsView, OrganizationAnomaliesView,
    OrganizationReportsView
)

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('<int:pk>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<int:pk>/users/', OrganizationUsersView.as_view(), name='organization-users'),
    path('<int:pk>/statistics/', OrganizationStatisticsView.as_view(), name='organization-statistics'),
    path('<int:pk>/unassigned-employees/', OrganizationUnassignedEmployeesView.as_view(), name='organization-unassigned-employees'),
    path('<int:pk>/unassigned-sites/', OrganizationUnassignedSitesView.as_view(), name='organization-unassigned-sites'),
    path('<int:pk>/sites/', OrganizationSitesView.as_view(), name='organization-sites'),
    path('<int:pk>/assign-site/', assign_site_to_organization, name='organization-assign-site'),
    path('<int:pk>/timesheets/', OrganizationTimesheetsView.as_view(), name='organization-timesheets'),
    path('<int:pk>/anomalies/', OrganizationAnomaliesView.as_view(), name='organization-anomalies'),
    path('<int:pk>/reports/', OrganizationReportsView.as_view(), name='organization-reports'),
]

