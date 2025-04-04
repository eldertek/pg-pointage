.PHONY: help setup-backend setup-frontend run-backend run-frontend migrate makemigrations test-backend test-frontend lint-backend lint-frontend clean

# Variables
PYTHON = python3
PIP = pip3
NPM = npm
DJANGO_MANAGE = $(PYTHON) backend/manage.py
VENV = .venv
VENV_ACTIVATE = . $(VENV)/bin/activate

help:
	@echo "Commandes disponibles:"
	@echo "  setup-backend    - Installer les dépendances backend"
	@echo "  setup-frontend   - Installer les dépendances frontend"
	@echo "  run-backend      - Lancer le serveur Django"
	@echo "  run-frontend     - Lancer le serveur de développement Vue.js"
	@echo "  migrate          - Appliquer les migrations Django"
	@echo "  makemigrations   - Créer les migrations Django"
	@echo "  test-backend     - Exécuter les tests backend"
	@echo "  test-frontend    - Exécuter les tests frontend"
	@echo "  lint-backend     - Vérifier le code backend"
	@echo "  lint-frontend    - Vérifier le code frontend"
	@echo "  clean            - Nettoyer les fichiers temporaires"

setup-backend:
	@echo "Installation des dépendances backend..."
	$(PYTHON) -m venv $(VENV)
	$(VENV_ACTIVATE) && $(PIP) install -r backend/requirements.txt

setup-frontend:
	@echo "Installation des dépendances frontend..."
	cd frontend && $(NPM) install

run-backend:
	@echo "Lancement du serveur Django..."
	$(VENV_ACTIVATE) && $(DJANGO_MANAGE) runserver

run-frontend:
	@echo "Lancement du serveur de développement Vue.js..."
	cd frontend && $(NPM) run dev

migrate:
	@echo "Application des migrations..."
	$(VENV_ACTIVATE) && $(DJANGO_MANAGE) migrate

makemigrations:
	@echo "Création des migrations..."
	$(VENV_ACTIVATE) && $(DJANGO_MANAGE) makemigrations

test-backend:
	@echo "Exécution des tests backend..."
	$(VENV_ACTIVATE) && $(DJANGO_MANAGE) test

test-frontend:
	@echo "Exécution des tests frontend..."
	cd frontend && $(NPM) run test

lint-backend:
	@echo "Vérification du code backend..."
	$(VENV_ACTIVATE) && flake8 backend

lint-frontend:
	@echo "Vérification du code frontend..."
	cd frontend && $(NPM) run lint

clean:
	@echo "Nettoyage des fichiers temporaires..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +

