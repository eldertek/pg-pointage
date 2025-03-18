from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Q
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import logging

from core.models import Site, User

# Configuration du logger
logger = logging.getLogger('planete_pointage')

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class BaseAutocompleteView(View):
    """
    Vue de base pour l'autocomplétion avec validation et gestion d'erreurs
    """
    model = None
    search_fields = None
    min_length = 1
    max_results = 10

    def validate_term(self, term):
        """Valide le terme de recherche"""
        if not term or len(term) < self.min_length:
            return None
        
        # Vérification des caractères spéciaux dangereux
        dangerous_chars = ['<', '>', ';', '=', '(', ')', '{', '}', '[', ']']
        if any(char in term for char in dangerous_chars):
            return None
        
        return term.strip()

    def get_queryset(self, term):
        """Retourne le queryset filtré"""
        if not self.model or not self.search_fields:
            return self.model.objects.none()

        # Construction de la requête Q pour la recherche
        query = Q()
        for field in self.search_fields:
            query |= Q(**{f"{field}__icontains": term})
        
        return self.model.objects.filter(query)[:self.max_results]

    def get(self, request, *args, **kwargs):
        """Gère la requête GET avec validation et gestion d'erreurs"""
        try:
            # Log de la requête pour débogage
            logger.info(f"Requête d'autocomplete reçue: {request.GET}")
            
            # Validation du terme de recherche
            term = self.validate_term(request.GET.get('term', ''))
            if not term:
                logger.info("Terme de recherche invalide, retour liste vide")
                return JsonResponse([], safe=False)
            
            # Récupération des résultats
            results = self.get_queryset(term)
            logger.info(f"Résultats trouvés: {results.count()}")
            
            # Formatage des résultats
            data = self.format_results(results)
            
            # Retour JSON direct sans passer par la vérification des permissions admin
            return JsonResponse(data, safe=False)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'autocomplétion : {str(e)}")
            return JsonResponse([], safe=False)

    def format_results(self, results):
        """
        Méthode à surcharger pour formater les résultats selon le modèle
        """
        raise NotImplementedError("La méthode format_results doit être implémentée")


class SiteAutocompleteView(BaseAutocompleteView):
    """
    Vue d'autocomplétion pour les sites
    """
    model = Site
    search_fields = ['name', 'adresse']

    def format_results(self, results):
        formatted = [
            {
                'id': site.id,
                'name': site.name,
                'text': f"{site.name} ({site.adresse})" if hasattr(site, 'adresse') and site.adresse else site.name
            }
            for site in results
        ]
        logger.info(f"Résultats formatés: {formatted}")
        return formatted
        
    def dispatch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class UserAutocompleteView(BaseAutocompleteView):
    """
    Vue d'autocomplétion pour les utilisateurs
    """
    model = User
    search_fields = ['username', 'first_name', 'last_name', 'email']

    def format_results(self, results):
        formatted = [
            {
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'text': user.username
            }
            for user in results
        ]
        logger.info(f"Résultats formatés: {formatted}")
        return formatted
        
    def dispatch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs) 