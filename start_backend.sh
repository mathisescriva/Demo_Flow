#!/bin/bash

# Script de démarrage du backend avec vérifications

cd "$(dirname "$0")"

echo "🚀 Démarrage du backend Lexia X..."
echo ""

# Trouver Ollama
OLLAMA_CMD=""
if command -v ollama &> /dev/null; then
    OLLAMA_CMD="ollama"
elif [ -f "/usr/local/bin/ollama" ]; then
    OLLAMA_CMD="/usr/local/bin/ollama"
elif [ -f "/opt/homebrew/bin/ollama" ]; then
    OLLAMA_CMD="/opt/homebrew/bin/ollama"
elif [ -f "/Applications/Ollama.app/Contents/Resources/ollama" ]; then
    OLLAMA_CMD="/Applications/Ollama.app/Contents/Resources/ollama"
fi

# Vérifier Ollama
if [ -z "$OLLAMA_CMD" ]; then
    echo "⚠️  Ollama n'est pas trouvé"
    echo "   Le backend démarrera mais l'endpoint /action ne fonctionnera pas"
else
    echo "✅ Ollama trouvé"
    # Vérifier si mistral est disponible
    if $OLLAMA_CMD list 2>/dev/null | grep -q "mistral"; then
        echo "✅ Modèle Mistral disponible"
    else
        echo "⚠️  Modèle Mistral non trouvé"
        echo "   Exécutez: $OLLAMA_CMD pull mistral"
    fi
fi

# Activer l'environnement virtuel
if [ ! -d "backend/venv" ]; then
    echo "❌ Environnement virtuel non trouvé"
    exit 1
fi

cd backend
source venv/bin/activate

echo ""
echo "🌟 Démarrage du serveur FastAPI sur http://localhost:8000"
echo "   Appuyez sur Ctrl+C pour arrêter"
echo ""

uvicorn main:app --reload
