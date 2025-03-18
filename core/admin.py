from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
import csv

from .models import User, Site, Pointage, Anomalie, StatistiquesTemps, Planning
from django.core.exceptions import ValidationError

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'get_role_with_icon', 'organisation', 'email', 'get_status']
    list_display_links = ['username', 'get_full_name']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'organisation__name']
    ordering = ['organisation', 'role', 'username']
    actions = ['activate_users', 'deactivate_users', 'export_users']
    
    fieldsets = [
        (None, {
            'fields': ('username', 'password'),
            'description': 'Identifiants de connexion. Le nom d\'utilisateur doit être unique.'
        }),
        ('Informations personnelles', {
            'fields': (('first_name', 'last_name'), 'email'),
            'description': 'Informations d\'identification de l\'utilisateur.'
        }),
        ('Rôle et organisation', {
            'fields': (('role', 'organisation'), 'is_active'),
            'description': 'Configuration du compte utilisateur.'
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser'),
            'classes': ('collapse',),
            'description': 'Permissions administratives spéciales.'
        })
    ]

    def get_list_display(self, request):
        """
        Retourne une liste des champs à afficher dans l'interface d'administration,
        en vérifiant qu'ils existent réellement dans la base de données.
        """
        # Liste par défaut
        display_fields = ['username', 'get_full_name', 'get_role_with_icon', 'organisation', 'email', 'get_status']
        
        # Vérifier si des champs n'existent pas dans la base de données
        model_fields = [f.name for f in self.model._meta.fields]
        for field in list(display_fields):
            # Ne vérifier que les champs du modèle (pas les méthodes)
            if not field.startswith('get_') and field not in model_fields and field != 'organisation':
                display_fields.remove(field)
                
        return display_fields
        
    def get_fields(self, request, obj=None):
        """
        Retourne la liste des champs à inclure dans le formulaire,
        en vérifiant qu'ils existent dans la base de données.
        """
        # Utiliser get_fieldsets au lieu de get_fields car nous utilisons fieldsets
        fieldsets = self.get_fieldsets(request, obj)
        fields = []
        
        # Extraire tous les champs des fieldsets
        for name, options in fieldsets:
            fields.extend(options.get('fields', []))
            
        # Aplatir les champs qui sont des tuples
        flat_fields = []
        for field in fields:
            if isinstance(field, tuple):
                flat_fields.extend(field)
            else:
                flat_fields.append(field)
        
        # Vérifier quels champs existent réellement
        db_fields = [f.name for f in self.model._meta.fields]
        return [f for f in flat_fields if f in db_fields]

    def get_full_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if full_name:
            return format_html('<strong>{}</strong>', full_name)
        return "-"
    get_full_name.short_description = "Nom complet"

    def get_role_with_icon(self, obj):
        icons = {
            'gardien': '👮',
            'agent_de_nettoyage': '🧹',
            'manager': '👔'
        }
        return format_html('<div class="role-badge role-{}">{} {}</div>', 
                         obj.role, 
                         icons.get(obj.role, ''), 
                         obj.get_role_display())
    get_role_with_icon.short_description = "Rôle"
    get_role_with_icon.admin_order_field = 'role'

    def get_status(self, obj):
        if not obj.is_active:
            return format_html('<div class="status-badge status-inactive">Inactif</div>')
        if obj.last_login and (timezone.now() - obj.last_login).days < 30:
            return format_html('<div class="status-badge status-active">Actif</div>')
        return format_html('<div class="status-badge status-warning">Inactif +30j</div>')
    get_status.short_description = "Statut"

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            if obj and obj.plannings.exists():
                return ['role'] + list(self.readonly_fields)
            return ['is_superuser', 'is_staff'] + list(self.readonly_fields)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        # Validation de l'organisation
        if not obj.organisation and request.user.organisation:
            obj.organisation = request.user.organisation
        
        # Validation du rôle manager
        if obj.role == 'manager' and not obj.is_staff:
            obj.is_staff = True
            messages.info(request, "Le statut 'staff' a été automatiquement activé pour ce manager.")
        
        super().save_model(request, obj, form, change)

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} utilisateurs ont été activés.")
    activate_users.short_description = "Activer les utilisateurs sélectionnés"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} utilisateurs ont été désactivés.")
    deactivate_users.short_description = "Désactiver les utilisateurs sélectionnés"

    def export_users(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=users-export-{datetime.now().strftime("%Y%m%d")}.csv'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Nom complet', 'Email', 'Rôle', 'Organisation', 'Statut', 'Dernier login'])
        
        for user in queryset:
            writer.writerow([
                user.username,
                f"{user.first_name} {user.last_name}".strip(),
                user.email,
                user.get_role_display(),
                user.organisation.name if user.organisation else '-',
                'Actif' if user.is_active else 'Inactif',
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '-'
            ])
        return response
    export_users.short_description = "Exporter les utilisateurs sélectionnés"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est une création
            if request.user.organisation:
                form.base_fields['organisation'].initial = request.user.organisation
        
        return form

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'organisation', 'get_email_alerts', 'get_status']
    list_display_links = ['name']
    search_fields = ['name', 'organisation__name', 'emails_alertes']
    ordering = ['organisation', 'name']
    actions = ['activate_sites', 'deactivate_sites', 'export_sites']
    
    def get_queryset(self, request):
        """Retourne uniquement les sites de l'organisation de l'utilisateur connecté"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Les superutilisateurs voient tous les sites
        if request.user.organisation:
            return qs.filter(organisation=request.user.organisation)
        return qs.none()  # Si l'utilisateur n'a pas d'organisation, il ne voit aucun site

    fieldsets = [
        (None, {
            'fields': (('name', 'organisation'),),
            'description': 'Informations principales du site. L\'organisation est obligatoire.'
        }),
        ('Identification', {
            'fields': ('qr_code_value',),
            'description': 'Code QR unique utilisé pour les pointages. Format requis : [ORGANISATION]-SITE-[00001]. Exemple : PG95-SITE-00001. Laissez vide pour une génération automatique.'
        }),
        ('Notifications', {
            'fields': ('emails_alertes',),
            'description': 'Adresses email qui recevront les alertes (une par ligne)'
        })
    ]

    def clean_qr_code_value(self, value, org_name):
        """Valide le format du code QR"""
        if not value:
            return value
            
        # Vérifier le format
        parts = value.split('-')
        if len(parts) != 3 or parts[1] != 'SITE' or len(parts[2]) != 5:
            raise ValidationError(
                'Le format du code doit être [ORGANISATION]-SITE-[00001]. '
                'Exemple : PG95-SITE-00001'
            )
            
        # Vérifier que l'organisation correspond
        if parts[0] != org_name:
            raise ValidationError(
                f'Le préfixe du code ({parts[0]}) doit correspondre au nom de l\'organisation ({org_name})'
            )
            
        # Vérifier que le numéro est bien un nombre sur 5 chiffres entre 00001 et 99999
        try:
            num = int(parts[2])
            if num < 1 or num > 99999 or len(parts[2]) != 5:
                raise ValueError
        except ValueError:
            raise ValidationError(
                'Le numéro doit être un nombre sur 5 chiffres entre 00001 et 99999.'
            )
            
        return value

    def get_email_alerts(self, obj):
        if not obj.emails_alertes:
            return format_html('<div class="status-badge status-warning">Aucun email</div>')
        emails = [e.strip() for e in obj.emails_alertes.split('\n') if e.strip()]
        return format_html(
            '<div class="status-badge status-active">{} email{}</div>',
            len(emails),
            's' if len(emails) > 1 else ''
        )
    get_email_alerts.short_description = "Alertes"

    def get_status(self, obj):
        plannings_actifs = obj.planning_set.filter(actif=True).count()
        if plannings_actifs > 0:
            return format_html(
                '<div class="status-badge status-active">{} planning{} actif{}</div>',
                plannings_actifs,
                's' if plannings_actifs > 1 else '',
                's' if plannings_actifs > 1 else ''
            )
        return format_html('<div class="status-badge status-inactive">Inactif</div>')
    get_status.short_description = "Statut"

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.planning_set.exists():
            return ['qr_code_value'] + list(self.readonly_fields)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        try:
            # Validation de l'organisation
            if not obj.organisation:
                raise ValidationError("L'organisation est obligatoire.")
            
            # Nettoyage et validation des emails
            if obj.emails_alertes:
                emails = []
                for email in obj.emails_alertes.split('\n'):
                    email = email.strip()
                    if email and '@' in email:  # Validation basique
                        emails.append(email)
                obj.emails_alertes = '\n'.join(emails)
            
            # Validation du format du code QR s'il est saisi manuellement
            if obj.qr_code_value:
                self.clean_qr_code_value(obj.qr_code_value, obj.organisation.name)
                # Vérifier si le code existe déjà
                if Site.objects.exclude(pk=obj.pk).filter(qr_code_value=obj.qr_code_value).exists():
                    raise ValidationError(f"Le code QR '{obj.qr_code_value}' existe déjà.")
            # Génération automatique du code QR si nécessaire
            else:
                # Récupérer le préfixe de l'organisation
                org_prefix = obj.organisation.name
                
                # Trouver le dernier numéro utilisé pour cette organisation
                pattern = f"{org_prefix}-SITE-"
                existing_sites = Site.objects.filter(
                    qr_code_value__startswith=pattern
                ).order_by('-qr_code_value')
                
                # Trouver le prochain numéro disponible
                next_number = 1
                if existing_sites.exists():
                    last_site = existing_sites.first()
                    try:
                        last_number = int(last_site.qr_code_value.split('-')[-1])
                        next_number = last_number + 1
                        # Vérifier si on a atteint la limite
                        if next_number > 99999:
                            raise ValidationError("Impossible de créer un nouveau site : le numéro maximum (99999) a été atteint pour cette organisation.")
                    except (ValueError, IndexError):
                        pass
                
                # Générer le nouveau code QR
                obj.qr_code_value = f"{org_prefix}-SITE-{str(next_number).zfill(5)}"
            
            super().save_model(request, obj, form, change)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return False

    def activate_sites(self, request, queryset):
        updated = 0
        for site in queryset:
            plannings = site.planning_set.filter(actif=False)
            plannings.update(actif=True)
            updated += plannings.count()
        self.message_user(request, f"{updated} plannings ont été activés.")
    activate_sites.short_description = "Activer les plannings des sites sélectionnés"

    def deactivate_sites(self, request, queryset):
        updated = 0
        for site in queryset:
            plannings = site.planning_set.filter(actif=True)
            plannings.update(actif=False)
            updated += plannings.count()
        self.message_user(request, f"{updated} plannings ont été désactivés.")
    deactivate_sites.short_description = "Désactiver les plannings des sites sélectionnés"

    def export_sites(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=sites-export-{datetime.now().strftime("%Y%m%d")}.csv'
        
        writer = csv.writer(response)
        writer.writerow(['Nom', 'Organisation', 'Code QR', 'Emails d\'alerte', 'Plannings actifs'])
        
        for site in queryset:
            plannings_actifs = site.planning_set.filter(actif=True).count()
            writer.writerow([
                site.name,
                site.organisation.name if site.organisation else '-',
                site.qr_code_value,
                site.emails_alertes.replace('\n', '; ') if site.emails_alertes else '-',
                plannings_actifs
            ])
        return response
    export_sites.short_description = "Exporter les sites sélectionnés"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Rendre l'organisation obligatoire
        form.base_fields['organisation'].required = True
        
        # Vérifier si le champ qr_code_value existe avant de le configurer
        if 'qr_code_value' in form.base_fields:
            # Rendre le qr_code_value optionnel
            form.base_fields['qr_code_value'].required = False
            
            # Aide à la saisie pour le code QR
            form.base_fields['qr_code_value'].help_text = (
                'Format requis : [ORGANISATION]-SITE-[00001]. '
                'Exemple : si votre organisation est "PG95", le code sera "PG95-SITE-00001". '
                'Laissez vide pour une génération automatique.'
            )
        
        # Personnalisation des widgets pour emails_alertes
        if 'emails_alertes' in form.base_fields:
            form.base_fields['emails_alertes'].widget.attrs.update({
                'placeholder': 'exemple@email.com\nautre@email.com',
                'rows': 4,
                'class': 'email-list-input'
            })
        
        return form

@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ['site', 'type', 'actif', 'user', 'get_jours_passage', 'get_horaires_resume']
    list_display_links = ['site']
    search_fields = ['site__name', 'user__username']
    ordering = ['site__name']
    change_form_template = 'admin/core/planning/change_form.html'
    
    def get_list_display(self, request):
        """
        Retourne une liste des champs à afficher dans l'interface d'administration,
        en vérifiant qu'ils existent réellement dans la base de données.
        """
        # Liste par défaut
        display_fields = ['site', 'type', 'actif', 'user', 'get_jours_passage', 'get_horaires_resume']
        
        # Vérifier si des champs n'existent pas dans la base de données
        model_fields = [f.name for f in self.model._meta.fields]
        for field in list(display_fields):
            # Ne vérifier que les champs du modèle (pas les méthodes)
            if not field.startswith('get_') and field not in model_fields:
                display_fields.remove(field)
                
        return display_fields
        
    def get_fields(self, request, obj=None):
        """
        Retourne la liste des champs à inclure dans le formulaire,
        en vérifiant qu'ils existent dans la base de données.
        """
        fields = super().get_fields(request, obj)
        db_fields = [f.name for f in self.model._meta.fields]
        
        # Filtrer pour n'inclure que les champs existants
        return [f for f in fields if f in db_fields]
    
    def get_list_filter(self, request):
        return []
    
    def get_jours_passage(self, obj):
        jours = []
        if obj.lundi: jours.append('Lun')
        if obj.mardi: jours.append('Mar')
        if obj.mercredi: jours.append('Mer')
        if obj.jeudi: jours.append('Jeu')
        if obj.vendredi: jours.append('Ven')
        if obj.samedi: jours.append('Sam')
        if obj.dimanche: jours.append('Dim')
        return ", ".join(jours) if jours else "-"
    get_jours_passage.short_description = "Jours de passage"
    
    def get_horaires_resume(self, obj):
        if obj.type == 'FIXE':
            matin = f"{obj.heure_debut_matin}-{obj.heure_fin_matin}" if obj.heure_debut_matin and obj.heure_fin_matin else ""
            aprem = f"{obj.heure_debut_aprem}-{obj.heure_fin_aprem}" if obj.heure_debut_aprem and obj.heure_fin_aprem else ""
            return f"{matin}, {aprem}".strip(", ")
        elif obj.type == 'FREQUENCE':
            return f"Durée min: {obj.duree_min} min"
        return "-"
    get_horaires_resume.short_description = "Horaires"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est une création
            form.base_fields['organisation'].initial = request.user.organisation
            
        # Messages d'aide personnalisés
        form.base_fields['actif'].help_text = "Désactiver temporairement le planning sans le supprimer"
        form.base_fields['site'].help_text = "Site auquel ce planning est associé"
        form.base_fields['user'].help_text = "Utilisateur responsable du planning"
        form.base_fields['type'].help_text = "FIXE: horaires fixes matin/après-midi, FREQUENCE: pointage à intervalle régulier"
        
        # Ordonner les listes déroulantes
        form.base_fields['site'].queryset = form.base_fields['site'].queryset.order_by('name')
        form.base_fields['user'].queryset = form.base_fields['user'].queryset.order_by('username')
        
        # Initialisation des valeurs par défaut
        if 'duree_min' in form.base_fields:
            form.base_fields['duree_min'].initial = None
        if 'marge_duree_pct' in form.base_fields:
            form.base_fields['marge_duree_pct'].initial = 10
            
        return form

    def get_fieldsets(self, request, obj=None):
        jours_fields = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        common_fields = ['actif', 'organisation', 'site', 'user', 'type']
        fixe_fields = ['heure_debut_matin', 'heure_fin_matin', 'heure_debut_aprem', 'heure_fin_aprem', 'marge_retard', 'marge_depart_anticip']
        frequence_fields = ['duree_min', 'marge_duree_pct']

        fieldsets = [
            ('Informations générales', {
                'fields': common_fields,
                'description': 'Configuration de base du planning'
            }),
            ('Jours de passage', {
                'fields': jours_fields,
                'description': 'Sélectionnez les jours de passage',
                'classes': ('days-fieldset',)
            })
        ]

        if obj:
            if obj.type == 'FIXE':
                fieldsets.append(('Paramètres horaires fixes', {
                    'fields': fixe_fields,
                    'description': 'Configuration des horaires fixes avec les plages du matin et de l\'après-midi',
                    'classes': ('type-fixe',)
                }))
            elif obj.type == 'FREQUENCE':
                fieldsets.append(('Paramètres de fréquence', {
                    'fields': frequence_fields,
                    'description': 'Configuration de la durée minimale de présence',
                    'classes': ('type-frequence',)
                }))
        else:
            fieldsets.extend([
                ('Paramètres horaires fixes', {
                    'fields': fixe_fields,
                    'classes': ('type-fixe',),
                    'description': 'Pour un planning à horaires fixes, définissez les plages horaires et les marges de tolérance'
                }),
                ('Paramètres de fréquence', {
                    'fields': frequence_fields,
                    'classes': ('type-frequence',),
                    'description': 'Pour un planning à fréquence, définissez la durée minimale de présence'
                })
            ])

        return fieldsets
        
@admin.register(Pointage)
class PointageAdmin(admin.ModelAdmin):
    list_display = ['user', 'site', 'date_scan', 'get_retard', 'get_depart_anticip', 'organisation']
    list_filter = ['organisation']
    search_fields = ['user__username', 'site__name']
    date_hierarchy = 'date_scan'
    
    def get_list_display(self, request):
        """
        Retourne une liste des champs à afficher dans l'interface d'administration,
        en vérifiant qu'ils existent réellement dans la base de données.
        """
        # Liste par défaut
        display_fields = ['user', 'site', 'date_scan', 'get_retard', 'get_depart_anticip', 'organisation']
        
        # Vérifier si des champs n'existent pas dans la base de données
        model_fields = [f.name for f in self.model._meta.fields]
        for field in list(display_fields):
            # Ne vérifier que les champs du modèle (pas les méthodes comme get_retard)
            if not field.startswith('get_') and field not in model_fields and field != 'organisation':
                display_fields.remove(field)
                
        return display_fields

    def get_queryset(self, request):
        """
        Retourne un queryset filtré par organisation si l'utilisateur n'est pas superuser.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.organisation:
            return qs.filter(organisation=request.user.organisation)
        elif not request.user.is_superuser:
            return qs.none()
        return qs
        
    def get_fields(self, request, obj=None):
        """
        Retourne la liste des champs à inclure dans le formulaire,
        en vérifiant qu'ils existent dans la base de données.
        """
        fields = super().get_fields(request, obj)
        db_fields = [f.name for f in self.model._meta.fields]
        
        # Filtrer pour n'inclure que les champs existants
        return [f for f in fields if f in db_fields]
    
    def get_retard(self, obj):
        if obj.retard > 0:
            return format_html('<span class="status-badge status-warning">{} min</span>', obj.retard)
        return '-'
    get_retard.short_description = "Retard"

    def get_depart_anticip(self, obj):
        if obj.depart_anticip > 0:
            return format_html('<span class="status-badge status-warning">{} min</span>', obj.depart_anticip)
        return '-'
    get_depart_anticip.short_description = "Départ anticipé"

@admin.register(Anomalie)
class AnomalieAdmin(admin.ModelAdmin):
    list_display = ['user', 'site', 'type_anomalie', 'get_status', 'get_date_declaration', 'organisation']
    list_filter = ['type_anomalie', 'status', 'organisation']
    search_fields = ['user__username', 'site__name', 'motif']
    date_hierarchy = 'date_creation'

    def get_list_display(self, request):
        """
        Retourne une liste des champs à afficher dans l'interface d'administration,
        en vérifiant qu'ils existent réellement dans la base de données.
        """
        # Liste par défaut
        display_fields = ['user', 'site', 'type_anomalie', 'get_status', 'get_date_declaration', 'organisation']
        
        # Vérifier si des champs n'existent pas dans la base de données
        model_fields = [f.name for f in self.model._meta.fields]
        for field in list(display_fields):
            # Ne vérifier que les champs du modèle (pas les méthodes comme get_status)
            if not field.startswith('get_') and field not in model_fields and field != 'organisation':
                display_fields.remove(field)
                
        return display_fields

    def get_queryset(self, request):
        """
        Retourne un queryset filtré par organisation si l'utilisateur n'est pas superuser.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.organisation:
            return qs.filter(organisation=request.user.organisation)
        elif not request.user.is_superuser:
            return qs.none()
        return qs
        
    def get_fields(self, request, obj=None):
        """
        Retourne la liste des champs à inclure dans le formulaire,
        en vérifiant qu'ils existent dans la base de données.
        """
        fields = super().get_fields(request, obj)
        db_fields = [f.name for f in self.model._meta.fields]
        
        # Filtrer pour n'inclure que les champs existants
        return [f for f in fields if f in db_fields]

    def get_status(self, obj):
        status_classes = {
            'en_attente': 'status-warning',
            'validee': 'status-active',
            'rejetee': 'status-inactive'
        }
        return format_html('<span class="status-badge {}">{}</span>', 
                         status_classes.get(obj.status, ''),
                         obj.get_status_display())
    get_status.short_description = "Statut"

    def get_date_declaration(self, obj):
        return obj.date_creation.strftime('%d/%m/%Y %H:%M')
    get_date_declaration.short_description = "Date de déclaration"

@admin.register(StatistiquesTemps)
class StatistiquesTempsAdmin(admin.ModelAdmin):
    list_display = ['user', 'site', 'mois', 'annee', 'get_heures_manquantes', 'get_details']
    list_filter = ['mois', 'annee', 'organisation']
    search_fields = ['user__username', 'site__name']
    ordering = ['-annee', '-mois']
    actions = ['recalculer_statistiques', 'export_statistiques']

    def get_list_display(self, request):
        """
        Retourne une liste des champs à afficher dans l'interface d'administration,
        en vérifiant qu'ils existent réellement dans la base de données.
        """
        # Liste par défaut
        display_fields = ['user', 'site', 'mois', 'annee', 'get_heures_manquantes', 'get_details']
        
        # Vérifier si des champs n'existent pas dans la base de données
        model_fields = [f.name for f in self.model._meta.fields]
        for field in list(display_fields):
            # Ne vérifier que les champs du modèle (pas les méthodes comme get_heures_manquantes)
            if not field.startswith('get_') and field not in model_fields and field != 'organisation':
                display_fields.remove(field)
                
        return display_fields
        
    def get_fields(self, request, obj=None):
        """
        Retourne la liste des champs à inclure dans le formulaire,
        en vérifiant qu'ils existent dans la base de données.
        """
        fields = super().get_fields(request, obj)
        db_fields = [f.name for f in self.model._meta.fields]
        
        # Filtrer pour n'inclure que les champs existants
        return [f for f in fields if f in db_fields]

    def get_heures_manquantes(self, obj):
        return obj.heures_manquantes
    get_heures_manquantes.short_description = "Heures manquantes"

    def get_details(self, obj):
        return format_html(
            '<div class="stats-details">'
            '<span class="stats-item stats-retard">Retard: {}</span> '
            '<span class="stats-item stats-depart">Départ: {}</span> '
            '<span class="stats-item stats-absence">Absence: {}</span>'
            '</div>',
            obj.heures_retard,
            obj.heures_depart_anticipe,
            obj.heures_absence
        )
    get_details.short_description = "Détails"

    def recalculer_statistiques(self, request, queryset):
        count = 0
        for stats in queryset:
            result = StatistiquesTemps.update_from_anomalies(
                user_id=stats.user.id,
                site_id=stats.site.id,
                date=timezone.datetime(stats.annee, stats.mois, 1)
            )
            if result:
                count += 1
        self.message_user(request, f"{count} statistiques ont été recalculées.")
    recalculer_statistiques.short_description = "Recalculer les statistiques sélectionnées"

    def export_statistiques(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=statistiques-{datetime.now().strftime("%Y%m%d")}.csv'
        
        writer = csv.writer(response)
        writer.writerow([
            'Utilisateur', 'Site', 'Organisation', 'Mois', 'Année',
            'Heures travaillées', 'Heures manquantes', 'Heures retard', 'Heures départ anticipé', 'Heures absence', 'Jours travaillés'
        ])
        
        for stats in queryset:
            writer.writerow([
                stats.user.username,
                stats.site.name,
                stats.organisation.name if stats.organisation else '-',
                stats.mois,
                stats.annee,
                stats.heures_travaillees,
                stats.heures_manquantes,
                stats.heures_retard,
                stats.heures_depart_anticipe,
                stats.heures_absence,
                stats.jours_travailles
            ])
        return response
    export_statistiques.short_description = "Exporter les statistiques sélectionnées"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(organisation=request.user.organisation)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['organisation'].initial = request.user.organisation
            form.base_fields['organisation'].disabled = True
        return form
