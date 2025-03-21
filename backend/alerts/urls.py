from django.urls import path
from .views import AlertListView, AlertDetailView

urlpatterns = [
    path('', AlertListView.as_view(), name='alert-list'),
    path('<int:pk>/', AlertDetailView.as_view(), name='alert-detail'),
]

