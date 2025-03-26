from django.db import transaction

def validate_site_id(site_id: str) -> bool:
    """
    Valide le format d'un ID de site.
    Format attendu : FFF-Sxxxx où :
    - FFF est l'ID de l'organisation sur 3 chiffres
    - S est la lettre S
    - xxxx est un nombre entre 0001 et 9999
    """
    if not site_id or '-' not in site_id:
        return False
    
    try:
        org_part, site_part = site_id.split('-')
        
        # Valider la partie organisation
        if not org_part.isdigit() or len(org_part) != 3:
            return False
        
        # Valider la partie site
        if not site_part.startswith('S') or len(site_part) != 5:
            return False
        
        site_number = int(site_part[1:])
        return 0 < site_number < 10000
    except (ValueError, IndexError):
        return False

def generate_site_id(organization) -> str:
    """
    Génère un ID unique pour un site au format 'FFF-Sxxxx'.
    Utilise une transaction pour éviter les conflits de concurrence.
    """
    from .models import Site  # Import local pour éviter l'import circulaire
    
    with transaction.atomic():
        # Récupérer le dernier ID utilisé pour cette organisation
        last_site = Site.objects.filter(
            nfc_id__startswith=f"{organization.org_id}-S"
        ).order_by('-nfc_id').first()
        
        if not last_site:
            # Premier site pour cette organisation
            return f"{organization.org_id}-S0001"
        
        try:
            # Extraire le numéro du dernier ID
            site_part = last_site.nfc_id.split('-')[1]
            last_number = int(site_part[1:])
            # Générer le prochain numéro
            next_number = last_number + 1
            if next_number >= 10000:
                raise ValueError("Limite de sites atteinte pour cette organisation")
            # Formater avec des zéros à gauche
            return f"{organization.org_id}-S{next_number:04d}"
        except (ValueError, IndexError):
            # En cas d'erreur de format, recommencer à S0001
            return f"{organization.org_id}-S0001" 