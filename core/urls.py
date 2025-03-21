from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'sites', views.SiteViewSet)
router.register(r'plannings', views.PlanningViewSet)
router.register(r'pointages', views.PointageViewSet)
router.register(r'anomalies', views.AnomalieViewSet)
router.register(r'statistiques', views.StatistiquesViewSet)

urlpatterns = [
    # API endpoints
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/login/', views.login_api, name='api-login'),
    path('api/v1/auth/logout/', views.logout_api, name='api-logout'),
    
    # Home page
    path('', views.home_view, name='home'),
] 