# Planète Gardiens Pointage

Application de gestion de pointage pour les gardiens et agents de nettoyage.

## 🎨 Design

- **Couleurs principales**
  - Bleu primaire : `#00346E`
  - Orange accent : `#F78C48`
  - Fond : `#FFFFFF`

## 🚀 Installation

### Prérequis

- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Redis (pour Celery)

### Configuration de l'environnement

1. Cloner le repository :
```bash
git clone <repository-url>
cd planete-pointage
```

2. Créer et configurer le fichier .env :
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

3. Installation complète :
```bash
make install
```

Cette commande va :
- Créer un environnement virtuel Python
- Installer les dépendances Python
- Installer les dépendances frontend
- Exécuter les migrations
- Collecter les fichiers statiques

## 🔧 Développement

### Lancer les serveurs de développement

```bash
# Lancer Django et Vue.js en même temps (nécessite tmux)
make dev

# Ou lancer séparément :
make run          # Serveur Django
make dev-frontend # Serveur Vue.js
```

### Commandes utiles

```bash
make migrate         # Appliquer les migrations
make test           # Lancer les tests
make lint           # Vérifier le code
make format         # Formater le code
make shell          # Shell Django
make createsuperuser # Créer un super utilisateur
```

## 📱 Application mobile (PWA)

L'application est accessible en PWA et peut être installée sur les appareils mobiles.
Elle fonctionne hors ligne avec synchronisation automatique.

### Fonctionnalités principales

- Pointage via NFC/QR Code
- Gestion des retards et départs anticipés
- Tableau de bord personnel
- Signalement d'anomalies
- Mode hors ligne

## 🔒 Sécurité

- Authentification par token JWT
- Gestion des rôles (Super Admin, Manager, Salarié)
- Traçabilité des modifications
- Chiffrement des données sensibles

## 📊 Rapports

- Exports CSV/PDF
- Statistiques de pointage
- Suivi des anomalies
- Rapports mensuels automatiques

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout d'une nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📝 License

Ce projet est sous licence [MIT](LICENSE). 