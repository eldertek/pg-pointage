from django.db import migrations, models
import django.db.models.deletion
from users.utils import generate_user_id

def update_user_ids_and_references(apps, schema_editor):
    """
    Mise à jour des IDs utilisateurs et des références
    """
    User = apps.get_model('users', 'User')
    
    # Mettre à jour tous les utilisateurs pour s'assurer qu'ils ont un employee_id valide
    for user in User.objects.all():
        if not user.employee_id:
            # Générer un nouvel ID et mettre à jour uniquement ce champ
            new_id = generate_user_id()
            User.objects.filter(pk=user.pk).update(employee_id=new_id)

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_update_user_ids'),
    ]

    operations = [
        # Exécuter la fonction pour s'assurer que tous les utilisateurs ont un employee_id
        migrations.RunPython(update_user_ids_and_references),
    ]
