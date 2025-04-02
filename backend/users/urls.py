""" URLs pour les utilisateurs """

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserLoginView, UserLogoutView, UserRegistrationView,
    UserProfileView, UserListView, UserDetailView, UserChangePasswordView,
    UserStatisticsView, UserSitesView, UserSchedulesView, UserReportsView
)

urlpatterns = [
    # Routes d'authentification
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', UserChangePasswordView.as_view(), name='change-password'),
    # Route profil utilisateur connecté
    path('profile/', UserProfileView.as_view(), name='profile'),
    # Routes CRUD utilisateurs
    path('', UserListView.as_view(), name='user-list'),
    # Routes détail utilisateur
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/statistics/', UserStatisticsView.as_view(), name='user-statistics'),
    path('<int:pk>/sites/', UserSitesView.as_view(), name='user-sites'),
    path('<int:pk>/schedules/', UserSchedulesView.as_view(), name='user-schedules'),
    path('<int:pk>/reports/', UserReportsView.as_view(), name='user-reports'),
]
