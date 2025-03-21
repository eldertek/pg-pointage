from django.urls import path
from .views import (
    OrganizationListView, OrganizationDetailView,
    OrganizationUsersView
)

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('<int:pk>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<int:pk>/users/', OrganizationUsersView.as_view(), name='organization-users'),
]

