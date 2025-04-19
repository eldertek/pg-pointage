from django.utils import timezone

def is_entity_active(entity):
    """
    Détermine si une entité est active en fonction de son statut et de ses dates d'activation.
    
    Règles:
    - Si les dates sont remplies, elles sont maîtresses sur le statut.
    - Si seule la date de début est renseignée : entité désactivée avant cette date et active à partir de cette date.
    - Si seule la date de fin est renseignée : entité active tout de suite et désactivée après la date de fin.
    - Si les deux dates sont renseignées : entité active uniquement entre ces deux dates.
    - S'il n'y a pas de date remplie, le statut renseigné de l'entité devient maître.
    
    Args:
        entity: L'entité à vérifier (User, Organization ou Site)
        
    Returns:
        bool: True si l'entité est active, False sinon
    """
    now = timezone.now().date()
    
    # Vérifier si l'entité a des dates d'activation
    has_start_date = hasattr(entity, 'activation_start_date') and entity.activation_start_date is not None
    has_end_date = hasattr(entity, 'activation_end_date') and entity.activation_end_date is not None
    
    # Si aucune date n'est définie, utiliser le statut is_active
    if not has_start_date and not has_end_date:
        return entity.is_active
    
    # Si seule la date de début est définie
    if has_start_date and not has_end_date:
        return now >= entity.activation_start_date
    
    # Si seule la date de fin est définie
    if not has_start_date and has_end_date:
        return now <= entity.activation_end_date
    
    # Si les deux dates sont définies
    return entity.activation_start_date <= now <= entity.activation_end_date
