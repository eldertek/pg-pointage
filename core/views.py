from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Pointage, Site, User, Anomalie, Planning, DateService
from .serializers import PointageSerializer, AnomalieSerializer
from .services import PointageService
from zoneinfo import ZoneInfo
import json
import logging
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler pour la console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Vue pour la page de connexion
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/admin/")  # Redirection correcte vers l'interface admin
        else:
            return render(request, "login.html", {"error": "Nom d'utilisateur ou mot de passe incorrect"})
    return render(request, "login.html")

@api_view(['POST'])
def create_pointage(request):
    """
    Reçoit un JSON:
    {
      "user_id": 1,
      "qr_code_value": "SITE_A",
      "date_scan": "2025-02-20T08:05:00Z"
    }
    """
    try:
        # Récupérer les données de la requête
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body.decode('utf-8'))
            
        logger.debug(f"[TRACKING DATE] Données reçues brutes: {data}")

        # Récupérer l'utilisateur et le site
        user = User.objects.get(id=data['user_id'])
        site = Site.objects.get(qr_code_value=data['qr_code_value'])
        
        # Convertir la date en timezone aware
        date_scan_str = data['date_scan'].replace('Z', '+00:00')
        logger.debug(f"[TRACKING DATE] Date string après nettoyage: {date_scan_str}")
        
        date_scan = timezone.datetime.fromisoformat(date_scan_str)
        logger.debug(f"[TRACKING DATE] Date après fromisoformat: {date_scan} (timezone: {date_scan.tzinfo})")
        
        date_scan = DateService.to_paris_timezone(date_scan)
        logger.debug(f"[TRACKING DATE] Date après conversion Paris: {date_scan} (timezone: {date_scan.tzinfo}, offset: {date_scan.utcoffset()})")

        # Conversion anglais -> français pour les jours
        DAYS_MAPPING = {
            'monday': 'lundi',
            'tuesday': 'mardi',
            'wednesday': 'mercredi',
            'thursday': 'jeudi',
            'friday': 'vendredi',
            'saturday': 'samedi',
            'sunday': 'dimanche'
        }
        jour_semaine = DAYS_MAPPING[date_scan.strftime("%A").lower()]
        logger.debug(f"[TRACKING DATE] Jour de la semaine: {jour_semaine}")
        
        # Récupérer le planning actif et la période
        planning, periode = PointageService.get_planning_actif(site, date_scan, jour_semaine)
        if not planning:
            logger.error(f"Pas de planning trouvé pour le site {site.name} le {jour_semaine}")
            return Response(
                {"error": "Pas de planning configuré pour ce jour sur ce site."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        logger.debug(f"[TRACKING DATE] Planning trouvé: {planning.id}, Type: {planning.type}, Période: {periode}")
        
        # Créer le pointage
        if periode:
            pointage = PointageService.creer_pointage(user, site, date_scan, planning, periode)
        else:
            logger.warning(f"Pointage hors plage horaire: {date_scan.strftime('%H:%M')}")
            pointage = PointageService.gerer_pointage_hors_plage(user, site, date_scan)
          
        logger.debug(f"[TRACKING DATE] Pointage créé - Date finale: {pointage.date_scan} (timezone: {pointage.date_scan.tzinfo})")

        # Sérialisation et réponse
        serializer = PointageSerializer(pointage)
        response_data = serializer.data
        logger.debug(f"[TRACKING DATE] Date dans la réponse: {response_data['date_scan']}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Erreur lors de la création du pointage: {str(e)}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_anomalie(request):
    data = request.data
    try:
        user = User.objects.get(id=data['user_id'])
        site = Site.objects.get(id=data['site_id']) if 'site_id' in data else None
        anomalie = Anomalie.objects.create(
            user=user, site=site, motif=data.get('motif', 'Non précisé'),
        )
        return Response(AnomalieSerializer(anomalie).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@login_required
def scan_qr_view(request):
    return render(request, "scan_qr.html")

@api_view(['POST'])
def create_pointage_via_qr(request):
    """
    Reçoit un JSON:
    {
        "user_id": 1,
        "qr_code_value": "SITE_A"
    }
    """
    try:
        data = request.data.copy()
        # Utiliser la date actuelle seulement pour les scans QR
        data['date_scan'] = timezone.localtime().isoformat()
        
        if hasattr(request, '_request'):
            request._request.POST = request._request.POST.copy()
            request._request.POST.update(data)
            return create_pointage(request._request)
        else:
            return create_pointage(request)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@staff_member_required
def ajax_filter_sites(request):
    organisation_id = request.GET.get('organisation')
    if organisation_id:
        sites = Site.objects.filter(organisation_id=organisation_id).values('id', 'name')
        return JsonResponse(list(sites), safe=False)
    return JsonResponse([], safe=False)

@staff_member_required
def ajax_filter_users(request):
    organisation_id = request.GET.get('organisation')
    if organisation_id:
        users = User.objects.filter(organisation_id=organisation_id).values('id', 'username')
        return JsonResponse(list(users), safe=False)
    return JsonResponse([], safe=False)

@staff_member_required
def site_autocomplete(request):
    term = request.GET.get('term', '')
    organisation = request.user.organisation
    logger.debug(f'Recherche site avec terme: {term}') # Debug
    
    # Recherche des sites correspondant au terme
    sites = Site.objects.filter(
        Q(name__icontains=term) | Q(adresse__icontains=term),
        organisation=organisation
    ).order_by('name')[:10]
    
    results = [{'id': site.id, 'name': site.name} for site in sites]
    logger.debug(f'Sites trouvés: {results}') # Debug
    return JsonResponse(results, safe=False)

@staff_member_required
def user_autocomplete(request):
    term = request.GET.get('term', '')
    organisation = request.user.organisation
    logger.debug(f'Recherche utilisateur avec terme: {term}') # Debug
    
    # Recherche des utilisateurs correspondant au terme
    users = User.objects.filter(
        Q(username__icontains=term) | 
        Q(first_name__icontains=term) | 
        Q(last_name__icontains=term),
        organisation=organisation
    ).order_by('username')[:10]
    
    results = [
        {
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip()
        } 
        for user in users
    ]
    logger.debug(f'Utilisateurs trouvés: {results}') # Debug
    return JsonResponse(results, safe=False)
