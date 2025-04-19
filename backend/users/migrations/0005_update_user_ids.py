from django.db import migrations
from users.utils import generate_user_id, validate_user_id

def update_user_ids(apps, schema_editor):
    """Met à jour les IDs des utilisateurs qui ne correspondent pas au format attendu"""
    User = apps.get_model('users', 'User')
    
    # Récupérer tous les utilisateurs
    users = User.objects.all()
    
    for user in users:
        # Si l'utilisateur n'a pas d'ID ou si l'ID n'est pas valide
        if not user.employee_id or not validate_user_id(user.employee_id):
            # Générer un nouvel ID
            new_id = generate_user_id()
            user.employee_id = new_id
            user.save()

def reverse_update_user_ids(apps, schema_editor):
    """Ne fait rien en cas de rollback car on ne peut pas restaurer les anciens IDs"""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0004_alter_user_employee_id'),
    ]

    operations = [
        migrations.RunPython(update_user_ids, reverse_update_user_ids),
    ] 