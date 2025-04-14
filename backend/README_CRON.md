# Configuration des tâches planifiées

Ce document explique comment configurer les tâches planifiées (cron jobs) pour le système de pointage.

## Vérification des pointages manquants

La commande `check_missed_checkins` vérifie tous les employés ayant un planning actif et crée des anomalies pour ceux qui n'ont pas pointé selon leur planning. Cette commande doit être exécutée tous les jours à minuit.

### Installation

1. Ouvrez le fichier crontab de l'utilisateur qui exécute l'application :

```bash
crontab -e
```

2. Ajoutez la ligne suivante (en remplaçant les chemins par les chemins réels) :

```
# Exécuter la commande check_missed_checkins tous les jours à minuit
0 0 * * * cd /chemin/vers/pg-pointage/backend && python manage.py check_missed_checkins --verbose >> /chemin/vers/pg-pointage/logs/check_missed_checkins.log 2>&1
```

3. Sauvegardez et fermez l'éditeur.

### Vérification

Pour vérifier que la tâche est correctement configurée :

```bash
crontab -l
```

### Test manuel

Pour tester manuellement la commande :

```bash
cd /chemin/vers/pg-pointage/backend
python manage.py check_missed_checkins --verbose
```

Pour tester la commande pour une date spécifique :

```bash
python manage.py check_missed_checkins --date 2023-04-01 --verbose
```

### Options disponibles

- `--date YYYY-MM-DD` : Vérifier les pointages manquants pour une date spécifique (par défaut : aujourd'hui)
- `--site ID` : Vérifier les pointages manquants pour un site spécifique (par défaut : tous les sites)
- `--employee ID` : Vérifier les pointages manquants pour un employé spécifique (par défaut : tous les employés)
- `--dry-run` : Exécuter en mode simulation sans modifier la base de données
- `--verbose` : Afficher des informations détaillées pendant l'exécution

## Logs

Les logs de la commande sont enregistrés dans le fichier `/chemin/vers/pg-pointage/logs/check_missed_checkins.log`. Assurez-vous que ce répertoire existe et que l'utilisateur qui exécute la commande a les droits d'écriture sur ce fichier.

Pour consulter les logs :

```bash
tail -f /chemin/vers/pg-pointage/logs/check_missed_checkins.log
```
