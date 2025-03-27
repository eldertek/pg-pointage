#!/bin/bash

# Fonction pour afficher les messages d'erreur en rouge
error() {
    echo -e "\e[31m$1\e[0m"
}

# Fonction pour afficher les messages de succès en vert
success() {
    echo -e "\e[32m$1\e[0m"
}

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    error "Environnement virtuel non trouvé. Création..."
    python -m venv .venv
fi

# Activer l'environnement virtuel Python
source .venv/bin/activate

# Installer les dépendances nécessaires
pip install drf-spectacular

# Aller dans le répertoire backend
cd backend || exit 1

# Générer le schéma OpenAPI avec Django
echo "Génération du schéma OpenAPI..."
python manage.py spectacular --file schema.yml
if [ ! -f "schema.yml" ]; then
    error "Erreur lors de la génération du schéma OpenAPI"
    exit 1
fi

success "Schéma OpenAPI généré avec succès"

# Créer le répertoire frontend/src/types/api s'il n'existe pas
mkdir -p ../frontend/src/types/api

# Copier le schéma dans le répertoire frontend
cp schema.yml ../frontend/schema.yml

# Aller dans le répertoire frontend
cd ../frontend || exit 1

# Installer openapi-typescript-codegen
echo "Installation de openapi-typescript-codegen..."
npm install --save-dev openapi-typescript-codegen

# Générer les types TypeScript
echo "Génération des types TypeScript..."
npx openapi-typescript-codegen --input schema.yml --output src/types/api

# Nettoyer
rm schema.yml
cd ../backend
rm schema.yml

success "Types TypeScript générés avec succès dans frontend/src/types/api/" 