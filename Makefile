.PHONY: help setup-backend setup-frontend run-backend run-frontend migrate makemigrations test-backend test-frontend lint-backend lint-frontend clean tests core users timesheets anomalies site-inactive schedule-inactive unplanned-day late-arrival early-departure frequency-insufficient consecutive-scans

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
	@echo "  tests            - Exécuter tous les tests"
	@echo "  tests core       - Exécuter les tests du module core"
	@echo "  tests users      - Exécuter les tests du module users"
	@echo "  tests timesheets - Exécuter les tests du module timesheets"
	@echo "  tests anomalies  - Exécuter tous les tests d'anomalies"
	@echo "  Tests spécifiques pour les règles d'anomalies (.cursor/rules/anomalies.mdc):"
	@echo "  tests site-inactive        - Tester la détection d'anomalie pour un site inactif"
	@echo "  tests schedule-inactive    - Tester la détection d'anomalie pour un planning inactif"
	@echo "  tests unplanned-day        - Tester la détection d'anomalie pour un jour non planifié"
	@echo "  tests late-arrival         - Tester la détection d'anomalie pour un retard"
	@echo "  tests early-departure      - Tester la détection d'anomalie pour un départ anticipé"
	@echo "  tests frequency-insufficient - Tester la détection d'anomalie pour une durée insuffisante"
	@echo "  tests consecutive-scans    - Tester la détection d'anomalie pour des scans consécutifs"
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

tests:
	@echo "Exécution des tests..."
	@if [ "$(filter core,$(MAKECMDGOALS))" = "core" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test core; \
	elif [ "$(filter users,$(MAKECMDGOALS))" = "users" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test users; \
	elif [ "$(filter timesheets,$(MAKECMDGOALS))" = "timesheets" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test timesheets; \
	elif [ "$(filter anomalies,$(MAKECMDGOALS))" = "anomalies" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree; \
	elif [ "$(filter site-inactive,$(MAKECMDGOALS))" = "site-inactive" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree.AnomalyDecisionTreeTestCase.test_inactive_site; \
	elif [ "$(filter schedule-inactive,$(MAKECMDGOALS))" = "schedule-inactive" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree.AnomalyDecisionTreeTestCase.test_inactive_schedule; \
	elif [ "$(filter unplanned-day,$(MAKECMDGOALS))" = "unplanned-day" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree.AnomalyDecisionTreeTestCase.test_unplanned_day; \
	elif [ "$(filter late-arrival,$(MAKECMDGOALS))" = "late-arrival" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree.AnomalyDecisionTreeTestCase.test_fixed_schedule_late_beyond_margin; \
	elif [ "$(filter early-departure,$(MAKECMDGOALS))" = "early-departure" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree.AnomalyDecisionTreeTestCase.test_fixed_schedule_early_departure_beyond_margin; \
	elif [ "$(filter frequency-insufficient,$(MAKECMDGOALS))" = "frequency-insufficient" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree.AnomalyDecisionTreeTestCase.test_frequency_schedule_insufficient_duration; \
	elif [ "$(filter consecutive-scans,$(MAKECMDGOALS))" = "consecutive-scans" ]; then \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test \
			timesheets.tests.test_anomaly_decision_tree.AnomalyDecisionTreeTestCase.test_consecutive_same_type_scans; \
	else \
		$(VENV_ACTIVATE) && cd backend && $(PYTHON) manage.py test; \
	fi

