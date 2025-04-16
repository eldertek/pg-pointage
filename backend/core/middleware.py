from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class UserLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to set the language based on the user's preference.
    
    This middleware checks:
    1. First, the Accept-Language header
    2. Then, if the user is authenticated, their language preference
    3. Finally, falls back to the default language
    """
    
    def process_request(self, request):
        # First check if the language is specified in the header
        language = request.META.get('HTTP_ACCEPT_LANGUAGE')
        
        # If the user is authenticated, use their language preference
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Get the user's language preference
                user_language = request.user.language
                if user_language:
                    language = user_language
            except AttributeError:
                # If the user model doesn't have a language field
                pass
        
        # If a valid language is found, activate it
        if language and language in [lang[0] for lang in settings.LANGUAGES]:
            translation.activate(language)
            request.LANGUAGE_CODE = language
        else:
            # Otherwise use the default language
            translation.activate(settings.LANGUAGE_CODE)
            request.LANGUAGE_CODE = settings.LANGUAGE_CODE
