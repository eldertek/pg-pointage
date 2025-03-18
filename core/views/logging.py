from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
import json
from ..utils.logging import logger, format_log_message

@csrf_protect
@require_http_methods(["POST"])
def client_log(request):
    """
    Vue pour recevoir et traiter les logs du client
    """
    try:
        log_data = json.loads(request.body)
        
        # Validation basique des données
        required_fields = ['level', 'message']
        if not all(field in log_data for field in required_fields):
            return JsonResponse({
                'status': 'error',
                'message': 'Champs requis manquants'
            }, status=400)

        # Ajout d'informations sur l'utilisateur
        if request.user.is_authenticated:
            log_data['user'] = {
                'id': request.user.id,
                'username': request.user.username
            }

        # Log selon le niveau
        level = log_data.get('level', 'info').lower()
        message = log_data.get('message')
        
        log_methods = {
            'debug': logger.debug,
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error
        }

        log_method = log_methods.get(level, logger.info)
        log_method(format_log_message(message, log_data))

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Format JSON invalide'
        }, status=400)
    except Exception as e:
        logger.error(format_log_message(
            "Erreur lors du traitement du log client",
            {'error': str(e)}
        ))
        return JsonResponse({
            'status': 'error',
            'message': 'Erreur interne du serveur'
        }, status=500) 