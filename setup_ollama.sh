#!/bin/bash

# Script pour configurer Ollama et télécharger le modèle Mistral

echo "🔧 Configuration d'Ollama pour Lexia X..."
echo ""

# Trouver Ollama
OLLAMA_CMD=""
if command -v ollama &> /dev/null; then
    OLLAMA_CMD="ollama"
    echo "✅ Ollama trouvé dans le PATH"
elif [ -f "/usr/local/bin/ollama" ]; then
    OLLAMA_CMD="/usr/local/bin/ollama"
    echo "✅ Ollama trouvé dans /usr/local/bin"
elif [ -f "/opt/homebrew/bin/ollama" ]; then
    OLLAMA_CMD="/opt/homebrew/bin/ollama"
    echo "✅ Ollama trouvé dans /opt/homebrew/bin"
elif [ -f "/Applications/Ollama.app/Contents/Resources/ollama" ]; then
    OLLAMA_CMD="/Applications/Ollama.app/Contents/Resources/ollama"
    echo "✅ Ollama trouvé dans Applications"
else
    echo "❌ Ollama n'est pas trouvé"
    echo ""
    echo "Veuillez :"
    echo "1. Installer Ollama depuis https://ollama.com"
    echo "2. Redémarrer votre terminal"
    echo "3. Relancer ce script"
    exit 1
fi

# Vérifier si Ollama fonctionne
echo "🔍 Vérification d'Ollama..."
if ! $OLLAMA_CMD --version &>/dev/null; then
    echo "⚠️  Ollama ne répond pas. Assurez-vous qu'il est démarré."
    echo "   Sur Mac, ouvrez l'application Ollama depuis Applications"
    exit 1
fi

echo "✅ Ollama fonctionne"
echo ""

# Vérifier les modèles disponibles
echo "📋 Modèles disponibles :"
$OLLAMA_CMD list
echo ""

# Vérifier si mistral est disponible
if $OLLAMA_CMD list 2>/dev/null | grep -q "mistral"; then
    echo "✅ Modèle Mistral déjà téléchargé"
    echo ""
    echo "🎉 Tout est prêt ! Vous pouvez démarrer la démo."
else
    echo "📥 Le modèle Mistral n'est pas téléchargé"
    echo "   Téléchargement en cours (cela peut prendre plusieurs minutes)..."
    echo ""
    
    $OLLAMA_CMD pull mistral
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Modèle Mistral téléchargé avec succès !"
        echo ""
        echo "🎉 Tout est prêt ! Vous pouvez démarrer la démo."
    else
        echo ""
        echo "❌ Erreur lors du téléchargement du modèle Mistral"
        echo "   Vérifiez votre connexion internet et réessayez"
        exit 1
    fi
fi

echo ""
echo "🚀 Pour démarrer la démo :"
echo "   Terminal 1: ./start_backend.sh"
echo "   Terminal 2: ./start_frontend.sh"
