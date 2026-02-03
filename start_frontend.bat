@echo off
REM Script de démarrage du frontend Lexia X (Windows)

echo 🎨 Démarrage du frontend Lexia X...
echo.

REM Vérifier si on est dans le bon répertoire
if not exist "frontend\package.json" (
    echo ❌ Erreur: Ce script doit être exécuté depuis la racine du projet
    exit /b 1
)

REM Aller dans le dossier frontend
cd frontend

REM Vérifier si node_modules existe
if not exist "node_modules" (
    echo 📦 Installation des dépendances npm...
    call npm install
)

REM Démarrer le serveur de développement
echo.
echo 🌟 Démarrage du serveur de développement sur http://localhost:5173
echo    Appuyez sur Ctrl+C pour arrêter
echo.
call npm run dev
