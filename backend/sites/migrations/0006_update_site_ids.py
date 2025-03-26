from django.db import migrations, models

def validate_site_id(site_id: str) -> bool:
    """
    Valide le format d'un ID de site.
    Format attendu : S suivi de 4 chiffres (S0001 à S9999)
    """
    if not site_id or len(site_id) != 5:
        return False
    
    if not site_id.startswith('S'):
        return False
    
    try:
        number = int(site_id[1:])
        return 0 < number < 10000
    except ValueError:
        return False

def update_site_ids(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    counter = 1
    
    # Mettre à jour tous les sites existants
    for site in Site.objects.all().order_by('created_at'):
        new_id = f'S{counter:04d}'
        # Vérifier que l'ID est valide avant de l'assigner
        if validate_site_id(new_id):
            site.nfc_id = new_id
            site.save()
            counter += 1

def reverse_site_ids(apps, schema_editor):
    # La réversion n'est pas nécessaire car les anciens IDs ne suivaient pas de format spécifique
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('sites', '0005_site_city_site_country_site_postal_code'),
    ]

    operations = [
        # D'abord mettre à jour les données avec les nouveaux IDs
        migrations.RunPython(update_site_ids, reverse_site_ids),
        
        # Ensuite seulement modifier la longueur du champ
        migrations.AlterField(
            model_name='site',
            name='nfc_id',
            field=models.CharField(
                max_length=5,
                unique=True,
                help_text='Format: S0001 à S9999',
                verbose_name='ID Site'
            ),
        ),
    ] 