from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from ...utils.logging import log_user_action
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_api(request):
    """
    API endpoint for user login.
    Returns JWT tokens for authentication.
    """
    username = request.data.get('username', None)
    password = request.data.get('password', None)
    
    if not username or not password:
        return Response(
            {"detail": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    user = authenticate(username=username, password=password)
    
    if user is None:
        log_user_action(None, 'login_failed', {'username': username, 'method': 'api'})
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    if not user.is_active:
        log_user_action(user, 'login_failed_inactive', {'method': 'api'})
        return Response(
            {"detail": "User account is disabled"},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    tokens = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
    
    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Serialize user information
    from ...serializers import UserSerializer
    user_data = UserSerializer(user).data
    
    # Log successful login
    log_user_action(user, 'login', {'method': 'api'})
    
    return Response({
        'tokens': tokens,
        'user': user_data
    })

@api_view(['POST'])
def logout_api(request):
    """
    API endpoint for user logout.
    Blacklists the refresh token.
    """
    try:
        refresh_token = request.data.get('refresh', None)
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        log_user_action(request.user, 'logout', {'method': 'api'})
        
        return Response({"detail": "Successfully logged out"})
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return Response(
            {"detail": "Invalid token"},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def token_refresh(request):
    """
    API endpoint for refreshing access tokens.
    """
    from rest_framework_simplejwt.serializers import TokenRefreshSerializer
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    
    serializer = TokenRefreshSerializer(data=request.data)
    
    try:
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
    except (InvalidToken, TokenError) as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        ) 