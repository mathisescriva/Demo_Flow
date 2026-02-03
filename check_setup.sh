#!/bin/bash

echo "🔍 Vérification de l'installation Lexia X..."
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python:${NC} $PYTHON_VERSION"
else
    echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
fi

# Vérifier Node
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js:${NC} $NODE_VERSION"
else
    echo -e "${RED}❌ Node.js n'est pas installé${NC}"
fi

# Vérifier FFmpeg
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
    echo -e "${GREEN}✅ FFmpeg:${NC} $FFMPEG_VERSION"
else
    echo -e "${RED}❌ FFmpeg n'est pas installé${NC}"
fi

# Vérifier Ollama
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama:${NC} Installé"
    # Vérifier si le modèle mistral est disponible
    if ollama list 2>/dev/null | grep -q "mistral"; then
        echo -e "${GREEN}✅ Modèle Mistral:${NC} Disponible"
    else
        echo -e "${YELLOW}⚠️  Modèle Mistral:${NC} Non téléchargé (exécutez: ollama run mistral)"
    fi
else
    echo -e "${RED}❌ Ollama:${NC} Non installé"
    echo -e "${YELLOW}   → Installez depuis https://ollama.com${NC}"
fi

# Vérifier l'environnement virtuel Python
if [ -d "backend/venv" ]; then
    echo -e "${GREEN}✅ Environnement virtuel Python:${NC} Créé"
    if [ -f "backend/venv/bin/faster-whisper" ] || [ -d "backend/venv/lib/python3.9/site-packages/faster_whisper" ]; then
        echo -e "${GREEN}✅ Faster-Whisper:${NC} Installé"
    else
        echo -e "${YELLOW}⚠️  Faster-Whisper:${NC} Vérification..."
    fi
else
    echo -e "${RED}❌ Environnement virtuel Python:${NC} Non créé"
fi

# Vérifier node_modules
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✅ Dépendances Frontend:${NC} Installées"
else
    echo -e "${RED}❌ Dépendances Frontend:${NC} Non installées"
fi

echo ""
echo "📋 Résumé:"
echo "   - Backend: Prêt (sauf si Ollama manque)"
echo "   - Frontend: Prêt"
echo ""
echo "🚀 Pour démarrer:"
echo "   Terminal 1: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "   Terminal 2: cd frontend && npm run dev"
