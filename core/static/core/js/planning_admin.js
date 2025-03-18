// Version sécurisée avec noConflict pour éviter les conflits jQuery
(function() {
    // Attendre que Django jQuery soit chargé
    function checkJQueryAndInit() {
        if (window.django && django.jQuery) {
            initPlanningAdmin(django.jQuery);
        } else {
            setTimeout(checkJQueryAndInit, 50);
        }
    }
    
    checkJQueryAndInit();
    
    function initPlanningAdmin($) {
        // Vérifier si l'initialisation de Select2 est désactivée
        if (window.DISABLE_PLANNING_ADMIN_SELECT2) {
            console.log("Initialisation de Select2 dans planning_admin.js désactivée");
        }
        
        // Sélecteurs des éléments
        var $organisationSelect = $('#id_organisation');
        var $siteSelect = $('#id_site');
        var $userSelect = $('#id_user');
        var $typeSelect = $('#id_type');
        var $joursPassage = $('.field-jours_passage');
        var $fixeFields = $('.field-heure_debut_matin, .field-heure_fin_matin, .field-heure_debut_aprem, .field-heure_fin_aprem, .field-marge_pop_up');
        var $frequenceFields = $('.field-duree_prevue_minutes');

        // Fonction pour mettre à jour les listes déroulantes site et user
        function updateSelects(organisationId) {
            if (!organisationId) return;

            // Mise à jour de la liste des sites - utiliser le nouvel endpoint d'autocomplete
            $.get('/api/autocomplete/site/', { term: '' })
                .done(function(data) {
                    $siteSelect.empty();
                    $siteSelect.append($('<option value="">---------</option>'));
                    
                    // Vérifier que data est un tableau avant d'utiliser forEach
                    if (Array.isArray(data)) {
                        data.forEach(function(site) {
                            $siteSelect.append($('<option></option>')
                                .attr('value', site.id)
                                .text(site.name || site.text));
                        });
                    } else {
                        console.error("Données de sites reçues au format incorrect:", data);
                    }
                })
                .fail(function(jqXHR, textStatus, errorThrown) {
                    console.error("Erreur lors de la récupération des sites:", textStatus, errorThrown);
                });

            // Mise à jour de la liste des utilisateurs - utiliser le nouvel endpoint d'autocomplete
            $.get('/api/autocomplete/user/', { term: '' })
                .done(function(data) {
                    $userSelect.empty();
                    $userSelect.append($('<option value="">---------</option>'));
                    
                    // Vérifier que data est un tableau avant d'utiliser forEach
                    if (Array.isArray(data)) {
                        data.forEach(function(user) {
                            $userSelect.append($('<option></option>')
                                .attr('value', user.id)
                                .text(user.username || user.text));
                        });
                    } else {
                        console.error("Données d'utilisateurs reçues au format incorrect:", data);
                    }
                })
                .fail(function(jqXHR, textStatus, errorThrown) {
                    console.error("Erreur lors de la récupération des utilisateurs:", textStatus, errorThrown);
                });
        }

        // Gestion de l'affichage des champs selon le type
        function updateFieldsVisibility() {
            var selectedType = $typeSelect.val();
            
            // Masquer tous les champs spécifiques
            $joursPassage.hide();
            $fixeFields.hide();
            $frequenceFields.hide();
            $('fieldset:contains("Paramètres horaires fixes")').hide();
            $('fieldset:contains("Paramètres de fréquence")').hide();

            // Afficher les champs selon le type sélectionné
            if (selectedType) {
                $joursPassage.show();
                if (selectedType === 'FIXE') {
                    $fixeFields.show();
                    $('fieldset:contains("Paramètres horaires fixes")').show();
                } else if (selectedType === 'FREQUENCE') {
                    $frequenceFields.show();
                    $('fieldset:contains("Paramètres de fréquence")').show();
                }
            }
        }

        // Supprimer les widgets "now"
        function removeNowWidgets() {
            $('.field-heure_debut_matin, .field-heure_fin_matin, .field-heure_debut_aprem, .field-heure_fin_aprem')
                .find('.datetimeshortcuts')
                .remove();
        }

        // Initialisation de Select2 pour les sélecteurs uniquement si ce n'est pas désactivé
        if (!window.DISABLE_PLANNING_ADMIN_SELECT2) {
            $('#id_site, #id_user').select2({
                width: '100%',
                language: {
                    noResults: function() {
                        return "Aucun résultat trouvé";
                    },
                    searching: function() {
                        return "Recherche en cours...";
                    }
                },
                sorter: function(data) {
                    return data.sort(function(a, b) {
                        return a.text.localeCompare(b.text);
                    });
                }
            });
        }

        // Event listeners
        $organisationSelect.on('change', function() {
            updateSelects($(this).val());
        });

        $typeSelect.on('change', updateFieldsVisibility);

        // Initialisation au chargement de la page
        if ($organisationSelect.val()) {
            updateSelects($organisationSelect.val());
        }

        // Exécuter après un court délai pour s'assurer que la page est complètement chargée
        setTimeout(function() {
            updateFieldsVisibility();
            removeNowWidgets();
        }, 100);
    }
})(); 