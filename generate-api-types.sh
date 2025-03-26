#!/bin/bash

# Activer l'environnement virtuel Python
source .venv/bin/activate

# Générer le schéma OpenAPI avec Django
cd backend
python manage.py spectacular --file schema.yml

# Installer openapi-typescript-codegen si nécessaire
cd ../frontend
if ! [ -x "$(command -v openapi-typescript-codegen)" ]; then
  npm install openapi-typescript-codegen --save-dev
fi

# Générer les types TypeScript
npx openapi-typescript-codegen --input ../backend/schema.yml --output src/types/api

# Nettoyer
cd ../backend
rm schema.yml

echo "Types TypeScript générés avec succès dans frontend/src/types/api/" 