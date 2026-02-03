#!/bin/bash
# Whisper Flow - Desktop App Launcher

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Le backend n'est pas démarré!"
    echo "   Lance d'abord: cd ../backend && ./start_backend.sh"
    exit 1
fi

echo "🚀 Lancement de Whisper Flow..."
python whisper_flow.py
