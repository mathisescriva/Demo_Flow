# ⚡ Whisper Flow

Application desktop légère de dictée vocale avec transcription locale.

## Fonctionnalités

- 🎤 **Push-to-Talk** : Maintenir le bouton ou la touche Espace
- 🔄 **Auto-Paste** : Colle automatiquement le texte dans l'application active
- 🔒 **100% Local** : Utilise Whisper en local (souverain)
- 🪶 **Ultra léger** : Petite fenêtre flottante toujours visible

## Installation

```bash
# 1. Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur Mac/Linux
# ou: venv\Scripts\activate  # Sur Windows

# 2. Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

```bash
# 1. D'abord, lancer le backend Whisper
cd ../backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Puis lancer Whisper Flow
cd ../whisper-flow
source venv/bin/activate
python whisper_flow.py
```

Ou utiliser le script de lancement :
```bash
./start.sh
```

## Comment ça marche

1. **Ouvrir** une application où vous voulez écrire (Notes, Word, email, etc.)
2. **Cliquer** dans le champ de texte cible
3. **Maintenir** le bouton 🎤 ou la touche **Espace** dans Whisper Flow
4. **Parler** clairement
5. **Relâcher** - le texte est automatiquement collé !

## Raccourcis

| Action | Raccourci |
|--------|-----------|
| Enregistrer | Maintenir **Espace** ou **clic** sur le bouton |
| Déplacer la fenêtre | Glisser n'importe où |

## Permissions macOS

Sur macOS, vous devrez autoriser :
- **Microphone** : Pour l'enregistrement audio
- **Accessibilité** : Pour le collage automatique (Préférences Système > Sécurité > Accessibilité)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  Whisper Flow   │────▶│  Backend FastAPI │
│  (PyQt6 App)    │     │  (localhost:8000)│
└─────────────────┘     └──────────────────┘
        │                        │
        │ Auto-paste             │ Whisper ASR
        ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│  App Active     │     │  faster-whisper  │
│  (Notes, Word)  │     │  (local model)   │
└─────────────────┘     └──────────────────┘
```

## Dépendances

- Python 3.9+
- PyQt6 (interface graphique)
- sounddevice (capture audio)
- pynput (simulation clavier)
- pyperclip (presse-papiers)
- Backend Whisper sur localhost:8000
