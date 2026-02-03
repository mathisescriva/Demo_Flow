#!/bin/bash

# Script de démarrage automatique pour Lexia X Demo

echo "🚀 Démarrage de Lexia X Demo..."
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
    echo "⚠️  Ollama n'est pas trouvé dans le PATH"
    echo "   Assurez-vous qu'Ollama est installé et redémarrez votre terminal"
    echo "   Ou ajoutez Ollama au PATH manuellement"
    exit 1
fi

echo "✅ Ollama trouvé: $OLLAMA_CMD"

# Vérifier si le modèle mistral est disponible
echo "🔍 Vérification du modèle Mistral..."
if $OLLAMA_CMD list 2>/dev/null | grep -q "mistral"; then
    echo "✅ Modèle Mistral disponible"
else
    echo "📥 Téléchargement du modèle Mistral (cela peut prendre quelques minutes)..."
    $OLLAMA_CMD pull mistral
    if [ $? -eq 0 ]; then
        echo "✅ Modèle Mistral téléchargé avec succès"
    else
        echo "❌ Erreur lors du téléchargement du modèle Mistral"
        exit 1
    fi
fi

# Vérifier l'environnement virtuel
if [ ! -d "backend/venv" ]; then
    echo "❌ Environnement virtuel Python non trouvé"
    exit 1
fi

# Vérifier node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Dépendances frontend non trouvées"
    exit 1
fi

echo ""
echo "✅ Tout est prêt !"
echo ""
echo "📋 Pour démarrer la démo, ouvrez 2 terminaux :"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd $(pwd)/backend"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd $(pwd)/frontend"
echo "  npm run dev"
echo ""
echo "Puis ouvrez http://localhost:5173 dans votre navigateur"
echo ""
