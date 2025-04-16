# Configuration des tâches planifiées

Ce document explique comment configurer les tâches planifiées (cron jobs) pour le système de pointage.

## Sauvegarde de la base de données (quotidien)

La commande `backup_database` sauvegarde la base de données PostgreSQL dans un fichier SQL. Cette commande doit être exécutée tous les jours à 00h00 pour créer une sauvegarde quotidienne de la base de données.

### Installation

1. Ouvrez le fichier crontab de l'utilisateur qui exécute l'application :

```bash
crontab -e
```

2. Ajoutez la ligne suivante (en remplaçant les chemins par les chemins réels) :

```
# Exécuter la commande backup_database tous les jours à 00h00 pour sauvegarder la base de données
0 0 * * * cd /chemin/vers/pg-pointage/backend && python manage.py backup_database --verbose >> /chemin/vers/pg-pointage/logs/backup_database.log 2>&1
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
python manage.py backup_database --verbose
```

### Options disponibles

- `--backup-dir PATH` : Répertoire où stocker les sauvegardes (par défaut : /opt/pg-pointage/backups)
- `--database-url URL` : URL de connexion à la base de données (format: postgres://user:password@host:port/dbname)
- `--retention-days DAYS` : Nombre de jours pendant lesquels conserver les sauvegardes (par défaut : 30)
- `--dry-run` : Exécuter en mode simulation sans créer de sauvegarde
- `--verbose` : Afficher des informations détaillées pendant l'exécution

### Restauration d'une sauvegarde

Pour restaurer une sauvegarde :

```bash
# Arrêter l'application si elle est en cours d'exécution
sudo systemctl stop pg-pointage

# Restaurer la base de données avec les paramètres de connexion
pg_restore --clean --if-exists --host localhost --port 5432 --username pguser --dbname pg_pointage /opt/pg-pointage/backups/pg_pointage_YYYYMMDD_HHMMSS.sql

# Ou restaurer avec DATABASE_URL
export PGPASSWORD=password
pg_restore --clean --if-exists --dbname postgres://user:password@host:port/dbname /opt/pg-pointage/backups/pg_pointage_YYYYMMDD_HHMMSS.sql

# Redémarrer l'application
sudo systemctl start pg-pointage
```

## Vérification des pointages manquants (quotidien)

La commande `check_missed_checkins` vérifie tous les employés ayant un planning actif et crée des anomalies pour ceux qui n'ont pas pointé selon leur planning. Cette commande doit être exécutée tous les jours à 00h10 pour vérifier les pointages de la veille (J-1).

### Installation

1. Ouvrez le fichier crontab de l'utilisateur qui exécute l'application :

```bash
crontab -e
```

2. Ajoutez la ligne suivante (en remplaçant les chemins par les chemins réels) :

```
# Exécuter la commande check_missed_checkins tous les jours à 00h10 pour vérifier les pointages de la veille
10 0 * * * cd /chemin/vers/pg-pointage/backend && python manage.py check_missed_checkins --verbose >> /chemin/vers/pg-pointage/logs/check_missed_checkins.log 2>&1
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

## Vérification des pointages manquants en temps réel (toutes les minutes)

La commande `check_minute_anomalies` vérifie en temps réel si des employés ont manqué leur pointage d'arrivée. Cette commande doit être exécutée toutes les minutes.

### Installation

1. Ouvrez le fichier crontab de l'utilisateur qui exécute l'application :

```bash
crontab -e
```

2. Ajoutez la ligne suivante (en remplaçant les chemins par les chemins réels) :

```
# Exécuter la commande check_minute_anomalies toutes les minutes
* * * * * cd /chemin/vers/pg-pointage/backend && python manage.py check_minute_anomalies >> /chemin/vers/pg-pointage/logs/check_minute_anomalies.log 2>&1
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
python manage.py check_minute_anomalies --verbose
```

### Options disponibles

- `--site ID` : Vérifier les pointages manquants pour un site spécifique (par défaut : tous les sites)
- `--employee ID` : Vérifier les pointages manquants pour un employé spécifique (par défaut : tous les employés)
- `--dry-run` : Exécuter en mode simulation sans modifier la base de données
- `--verbose` : Afficher des informations détaillées pendant l'exécution

## Fonctionnalités implémentées

### Détection d'anomalies par minute

La commande `check_minute_anomalies` implémente la logique définie dans `.cursor/rules/minute_anomalies.mdc`. Elle vérifie en temps réel si des employés ont manqué leur pointage d'arrivée et crée des anomalies en conséquence.

### Gestion des plannings demi-journée

Le système gère désormais correctement les plannings demi-journée (matin et après-midi) en distinguant les types de journée (FULL, AM, PM) et en appliquant les règles spécifiques à chaque type.

### Détection d'anomalies pour les plannings de type fréquence

Le système vérifie si le temps passé est inférieur à la durée prévue dans les plannings de type fréquence, en tenant compte de la marge de tolérance configurée.

### Mise à jour des anomalies existantes

Lorsqu'un employé pointe en retard ou part plus tôt, le système met à jour les anomalies existantes (MISSING_ARRIVAL ou MISSING_DEPARTURE) au lieu d'en créer de nouvelles, ce qui évite les doublons.

### Gestion des scans multiples

Le système détecte les scans multiples (plus de pointages que prévu) et crée des anomalies de type CONSECUTIVE_SAME_TYPE avec une description détaillée.

## Logs

Les logs des commandes sont enregistrés dans les fichiers suivants :

- `/chemin/vers/pg-pointage/logs/backup_database.log` pour la sauvegarde quotidienne de la base de données
- `/chemin/vers/pg-pointage/logs/check_missed_checkins.log` pour la vérification quotidienne des pointages manquants
- `/chemin/vers/pg-pointage/logs/check_minute_anomalies.log` pour la vérification par minute des pointages manquants

Assurez-vous que ce répertoire existe et que l'utilisateur qui exécute les commandes a les droits d'écriture sur ces fichiers.

Pour consulter les logs :

```bash
tail -f /chemin/vers/pg-pointage/logs/backup_database.log
tail -f /chemin/vers/pg-pointage/logs/check_missed_checkins.log
tail -f /chemin/vers/pg-pointage/logs/check_minute_anomalies.log
```
