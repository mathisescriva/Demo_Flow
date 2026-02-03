#!/bin/bash

# Script de démarrage du frontend

cd "$(dirname "$0")"

echo "🎨 Démarrage du frontend Lexia X..."
echo ""

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Dépendances frontend non trouvées"
    echo "   Exécutez: cd frontend && npm install"
    exit 1
fi

cd frontend

echo "🌟 Démarrage du serveur de développement sur http://localhost:5173"
echo "   Appuyez sur Ctrl+C pour arrêter"
echo ""

npm run dev
