from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class UserLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to set the language based on the user's preference.

    This middleware checks:
    1. If the user is authenticated, use their language preference
    2. Otherwise, fall back to the default language
    """

    def process_request(self, request):
        # Initialize language to None
        language = None

        # If the user is authenticated, use their language preference
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Get the user's language preference
                language = request.user.language
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
