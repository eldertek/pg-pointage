# Force l'utilisation de bash
SHELL := /bin/bash

.PHONY: install migrate run test shell clean frontend serve dev create-venv install-deps install-frontend collectstatic clean-static help

# Variables
PYTHON = python3
MANAGE = $(PYTHON) manage.py
PIP = pip
VENV = venv
ACTIVATE = . $(VENV)/bin/activate
NPM = npm
PROJECT_NAME = planete_pointage

# Installation de l'environnement complet
install: create-venv install-deps install-frontend migrate collectstatic

# Création de l'environnement virtuel Python
create-venv:
	test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && $(PIP) install --upgrade pip

# Installation des dépendances Python
install-deps:
	$(ACTIVATE) && $(PIP) install -r requirements.txt

# Installation et build du frontend
install-frontend:
	cd frontend/pointage-app && $(NPM) install
	$(MAKE) frontend

# Migrations de la base de données
migrate:
	$(ACTIVATE) && $(MANAGE) makemigrations
	$(ACTIVATE) && $(MANAGE) migrate

# Compilation du frontend
frontend:
	cd frontend/pointage-app && $(NPM) run build

# Collecte des fichiers statiques
collectstatic:
	$(ACTIVATE) && $(MANAGE) collectstatic --noinput

# Nettoyage des fichiers statiques
clean-static:
	rm -rf static/frontend
	rm -rf staticfiles

# Lancement du serveur Django
run:
	$(ACTIVATE) && $(MANAGE) runserver 0.0.0.0:8000

# Lancement du serveur de développement frontend
dev-frontend:
	cd frontend/pointage-app && $(NPM) run dev

# Lancement des deux serveurs en développement (nécessite tmux)
dev: clean-static frontend collectstatic
	tmux kill-session -t pointage 2>/dev/null || true
	tmux new-session -d -s pointage '$(MAKE) run' \; \
	split-window -h '$(MAKE) dev-frontend' \; \
	attach

# Commande tout-en-un pour la production
serve: clean-static frontend collectstatic
	$(ACTIVATE) && $(MANAGE) runserver 0.0.0.0:8000

# Tests
test:
	$(ACTIVATE) && $(MANAGE) test

# Shell Django
shell:
	$(ACTIVATE) && $(MANAGE) shell

# Nettoyage des fichiers compilés
clean: clean-static
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -r {} +
	rm -rf frontend/pointage-app/dist

# Création d'un superutilisateur
createsuperuser:
	$(ACTIVATE) && $(MANAGE) createsuperuser

# Vérification de la syntaxe Python
lint:
	$(ACTIVATE) && flake8 .
	$(ACTIVATE) && black . --check

# Formatage du code
format:
	$(ACTIVATE) && black .

# Aide
help:
	@echo "Commandes disponibles:"
	@echo "  make install          - Installation complète (venv, dépendances, frontend, migrations)"
	@echo "  make create-venv      - Crée l'environnement virtuel Python"
	@echo "  make install-deps     - Installe les dépendances Python"
	@echo "  make install-frontend - Installe les dépendances frontend"
	@echo "  make migrate          - Crée et applique les migrations"
	@echo "  make frontend         - Compile le frontend"
	@echo "  make collectstatic    - Collecte les fichiers statiques"
	@echo "  make clean-static     - Nettoie les fichiers statiques"
	@echo "  make run             - Lance le serveur Django"
	@echo "  make dev-frontend     - Lance le serveur de développement frontend"
	@echo "  make dev             - Lance les deux serveurs en développement (Django + Vue)"
	@echo "  make serve           - Prépare et lance l'application en mode production"
	@echo "  make test            - Lance les tests"
	@echo "  make shell           - Lance le shell Django"
	@echo "  make clean           - Nettoie les fichiers compilés"
	@echo "  make createsuperuser - Crée un superutilisateur"
	@echo "  make lint            - Vérifie la syntaxe du code"
	@echo "  make format          - Formate le code avec black"
	
