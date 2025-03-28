from django.urls import path
from .views import (
    OrganizationListView, OrganizationDetailView,
    OrganizationUsersView, OrganizationStatisticsView,
    OrganizationUnassignedEmployeesView, OrganizationUnassignedSitesView
)

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('<int:pk>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<int:pk>/users/', OrganizationUsersView.as_view(), name='organization-users'),
    path('<int:pk>/statistics/', OrganizationStatisticsView.as_view(), name='organization-statistics'),
    path('<int:pk>/unassigned-employees/', OrganizationUnassignedEmployeesView.as_view(), name='organization-unassigned-employees'),
    path('<int:pk>/unassigned-sites/', OrganizationUnassignedSitesView.as_view(), name='organization-unassigned-sites'),
]

