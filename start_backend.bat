@echo off
REM Script de démarrage du backend Lexia X (Windows)

echo 🚀 Démarrage du backend Lexia X...
echo.

REM Vérifier si on est dans le bon répertoire
if not exist "backend\main.py" (
    echo ❌ Erreur: Ce script doit être exécuté depuis la racine du projet
    exit /b 1
)

REM Aller dans le dossier backend
cd backend

REM Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo 📦 Création de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
echo 🔧 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances si nécessaire
if not exist "venv\.dependencies_installed" (
    echo 📥 Installation des dépendances...
    pip install -r requirements.txt
    type nul > venv\.dependencies_installed
)

REM Vérifier Ollama
echo 🔍 Vérification d'Ollama...
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Ollama n'est pas installé ou pas dans le PATH
    echo    Installez Ollama depuis https://ollama.com
    echo    Puis exécutez: ollama run mistral
) else (
    echo ✅ Ollama détecté
)

REM Démarrer le serveur
echo.
echo 🌟 Démarrage du serveur FastAPI sur http://localhost:8000
echo    Appuyez sur Ctrl+C pour arrêter
echo.
uvicorn main:app --reload
