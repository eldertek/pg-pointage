# Planète Gardiens Pointage API

Ce document décrit l'API RESTful pour l'application Planète Gardiens Pointage. L'API permet de gérer les pointages, les sites, les plannings, les anomalies et les statistiques de temps.

## Authentification

L'API utilise l'authentification JWT (JSON Web Tokens). Pour accéder à l'API, vous devez d'abord obtenir un token d'accès.

### Obtenir un token

```
POST /api/token/
```

**Corps de la requête :**
```json
{
  "username": "utilisateur",
  "password": "mot_de_passe"
}
```

**Réponse :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Rafraîchir un token

```
POST /api/token/refresh/
```

**Corps de la requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Réponse :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Se déconnecter

```
POST /api/v1/auth/logout/
```

**Corps de la requête :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Points de terminaison principaux

### Utilisateurs

- `GET /api/v1/users/` - Liste des utilisateurs
- `POST /api/v1/users/` - Créer un utilisateur
- `GET /api/v1/users/{id}/` - Détails d'un utilisateur
- `PUT /api/v1/users/{id}/` - Mettre à jour un utilisateur
- `PATCH /api/v1/users/{id}/` - Mettre à jour partiellement un utilisateur
- `DELETE /api/v1/users/{id}/` - Supprimer un utilisateur
- `GET /api/v1/users/me/` - Informations sur l'utilisateur connecté
- `GET /api/v1/users/gardiens/` - Liste des gardiens
- `GET /api/v1/users/agents_nettoyage/` - Liste des agents de nettoyage
- `GET /api/v1/users/managers/` - Liste des managers

### Sites

- `GET /api/v1/sites/` - Liste des sites
- `POST /api/v1/sites/` - Créer un site
- `GET /api/v1/sites/{id}/` - Détails d'un site
- `PUT /api/v1/sites/{id}/` - Mettre à jour un site
- `PATCH /api/v1/sites/{id}/` - Mettre à jour partiellement un site
- `DELETE /api/v1/sites/{id}/` - Supprimer un site
- `GET /api/v1/sites/{id}/plannings/` - Liste des plannings pour un site
- `GET /api/v1/sites/{id}/pointages/` - Liste des pointages pour un site
- `GET /api/v1/sites/{id}/anomalies/` - Liste des anomalies pour un site
- `GET /api/v1/sites/{id}/verify_qr/` - Vérifier un QR code

### Plannings

- `GET /api/v1/plannings/` - Liste des plannings
- `POST /api/v1/plannings/` - Créer un planning
- `GET /api/v1/plannings/{id}/` - Détails d'un planning
- `PUT /api/v1/plannings/{id}/` - Mettre à jour un planning
- `PATCH /api/v1/plannings/{id}/` - Mettre à jour partiellement un planning
- `DELETE /api/v1/plannings/{id}/` - Supprimer un planning
- `GET /api/v1/plannings/user_plannings/` - Liste des plannings de l'utilisateur connecté
- `GET /api/v1/plannings/active/` - Liste des plannings actifs
- `POST /api/v1/plannings/{id}/toggle_active/` - Activer/désactiver un planning
- `GET /api/v1/plannings/by_date/` - Liste des plannings actifs pour une date spécifique

### Pointages

- `GET /api/v1/pointages/` - Liste des pointages
- `POST /api/v1/pointages/` - Créer un pointage
- `GET /api/v1/pointages/{id}/` - Détails d'un pointage
- `PUT /api/v1/pointages/{id}/` - Mettre à jour un pointage
- `PATCH /api/v1/pointages/{id}/` - Mettre à jour partiellement un pointage
- `DELETE /api/v1/pointages/{id}/` - Supprimer un pointage
- `GET /api/v1/pointages/today/` - Liste des pointages d'aujourd'hui
- `GET /api/v1/pointages/my_pointages/` - Liste des pointages de l'utilisateur connecté
- `POST /api/v1/pointages/scan_qr/` - Créer un pointage à partir d'un scan QR
- `GET /api/v1/pointages/with_anomalies/` - Liste des pointages avec anomalies

### Anomalies

- `GET /api/v1/anomalies/` - Liste des anomalies
- `POST /api/v1/anomalies/` - Créer une anomalie
- `GET /api/v1/anomalies/{id}/` - Détails d'une anomalie
- `PUT /api/v1/anomalies/{id}/` - Mettre à jour une anomalie
- `PATCH /api/v1/anomalies/{id}/` - Mettre à jour partiellement une anomalie
- `DELETE /api/v1/anomalies/{id}/` - Supprimer une anomalie
- `GET /api/v1/anomalies/unprocessed/` - Liste des anomalies non traitées
- `GET /api/v1/anomalies/my_anomalies/` - Liste des anomalies de l'utilisateur connecté
- `POST /api/v1/anomalies/{id}/process/` - Traiter une anomalie
- `POST /api/v1/anomalies/declare/` - Déclarer une nouvelle anomalie

### Statistiques

- `GET /api/v1/statistiques/` - Liste des statistiques
- `GET /api/v1/statistiques/{id}/` - Détails d'une statistique
- `GET /api/v1/statistiques/my_stats/` - Statistiques de l'utilisateur connecté
- `GET /api/v1/statistiques/summary/` - Résumé des statistiques
- `POST /api/v1/statistiques/recalculate/` - Recalculer les statistiques

## Documentation interactive

Une documentation interactive complète de l'API est disponible aux URLs suivantes :

- Swagger UI : `/swagger/`
- ReDoc : `/redoc/`
- OpenAPI Spec : `/swagger.json` 