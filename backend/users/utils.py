from django.db import transaction

def validate_user_id(user_id: str) -> bool:
    """
    Valide le format d'un ID utilisateur.
    Format attendu : UXXXXX où X est un chiffre entre 00001 et 99999
    """
    if not user_id or not user_id.startswith('U'):
        return False
    
    try:
        # Vérifier que le reste est un nombre
        user_number = int(user_id[1:])
        return 0 < user_number < 100000 and len(user_id) == 6
    except (ValueError, IndexError):
        return False

def generate_user_id() -> str:
    """
    Génère un ID unique pour un utilisateur au format 'UXXXXX'.
    Utilise une transaction pour éviter les conflits de concurrence.
    """
    from .models import User  # Import local pour éviter l'import circulaire
    
    with transaction.atomic():
        # Récupérer le dernier ID utilisé
        last_user = User.objects.filter(
            employee_id__startswith='U'
        ).order_by('-employee_id').first()
        
        if not last_user or not last_user.employee_id or not last_user.employee_id.startswith('U'):
            # Premier utilisateur ou pas d'ID valide
            return 'U00001'
        
        try:
            # Extraire le numéro du dernier ID
            last_number = int(last_user.employee_id[1:])
            # Générer le prochain numéro
            next_number = last_number + 1
            if next_number >= 100000:
                # Si on atteint la limite, recommencer à 1
                next_number = 1
            # Formater avec des zéros à gauche
            return f"U{next_number:05d}"
        except (ValueError, IndexError):
            # En cas d'erreur de format, recommencer à U00001
            return 'U00001'
