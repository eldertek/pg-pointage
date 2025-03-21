from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .users import UserViewSet, GroupViewSet
from .sites import SiteViewSet
from .plannings import PlanningViewSet
from .pointages import PointageViewSet
from .anomalies import AnomalieViewSet
from .statistiques import StatistiquesViewSet
from .auth import login_api, logout_api, token_refresh

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'sites', SiteViewSet)
router.register(r'plannings', PlanningViewSet)
router.register(r'pointages', PointageViewSet)
router.register(r'anomalies', AnomalieViewSet)
router.register(r'statistiques', StatistiquesViewSet)

# Create API URL patterns
urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/login/', login_api, name='api-login'),
    path('auth/logout/', logout_api, name='api-logout'),
    path('auth/refresh/', token_refresh, name='api-token-refresh'),
]
