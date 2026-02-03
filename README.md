# 🎙️ Lexia X - Démonstration End-to-End

Application de démonstration prouvant que **Lexia X** capture la parole en zone industrielle, la transcrit localement (Souveraineté) et exécute des actions dans un ERP/CRM via un modèle de langage (SLM) local.

## 🎯 Objectif de la Démo

Prouver le traitement **100% local et souverain** :
- ✅ Capture audio via microphone
- ✅ Transcription locale avec **Faster-Whisper**
- ✅ Analyse par **SLM local** (Ollama + Mistral/Llama3)
- ✅ Extraction structurée en JSON pour ERP/CRM

## 📋 Pré-requis

### 1. Installer Ollama

Téléchargez et installez Ollama depuis [ollama.com](https://ollama.com)

Une fois installé, téléchargez le modèle Mistral :
```bash
ollama run mistral
```

*(Cela téléchargera le modèle que le backend utilisera pour l'analyse)*

### 2. Installer FFmpeg

**Sur macOS :**
```bash
brew install ffmpeg
```

**Sur Windows :**
- Via Chocolatey : `choco install ffmpeg`
- Ou téléchargez l'exécutable depuis [ffmpeg.org](https://ffmpeg.org/download.html)

**Sur Linux (Ubuntu/Debian) :**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 3. Python 3.8+

Assurez-vous d'avoir Python 3.8 ou supérieur installé :
```bash
python --version
```

## 🚀 Installation et Démarrage

### Backend (FastAPI)

1. **Naviguer vers le dossier backend :**
```bash
cd backend
```

2. **Créer un environnement virtuel (recommandé) :**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances :**
```bash
pip install -r requirements.txt
```

4. **Démarrer le serveur :**
```bash
uvicorn main:app --reload
```

Le backend sera accessible sur `http://localhost:8000`

**Note :** Pour utiliser le GPU avec Whisper (si disponible), définissez la variable d'environnement :
```bash
export USE_GPU=true  # Sur Windows: set USE_GPU=true
uvicorn main:app --reload
```

### Frontend (React + Vite)

1. **Ouvrir un nouveau terminal et naviguer vers le dossier frontend :**
```bash
cd frontend
```

2. **Installer les dépendances :**
```bash
npm install
```

3. **Démarrer le serveur de développement :**
```bash
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173`

## 🎬 Utilisation

1. **Démarrer le backend** (terminal 1)
2. **Démarrer le frontend** (terminal 2)
3. **Ouvrir votre navigateur** sur `http://localhost:5173`
4. **Autoriser l'accès au microphone** lorsque demandé
5. **Cliquer sur "Démarrer l'enregistrement"**
6. **Parler votre message** (exemple : *"Hugo ici, j'ai une fuite sur la vanne V12, commande un kit de joint et mets l'alerte au max"*)
7. **Cliquer sur "Arrêter l'enregistrement"**

### Scénario de Test

**Message vocal :**
> "Hugo ici, j'ai une fuite sur la vanne V12, commande un kit de joint et mets l'alerte au max"

**Résultat attendu dans l'ERP :**
- **Objet :** Vanne V12
- **Référence Pièce :** Kit de joint V12
- **Gravité :** 5/5 (Urgente)
- **Action Requise :** Commander kit de joint et mettre alerte au maximum

## 📁 Structure du Projet

```
Demo_Flow/
├── backend/
│   ├── main.py              # API FastAPI avec endpoints /transcribe et /action
│   └── requirements.txt      # Dépendances Python
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Composant principal React
│   │   ├── main.tsx         # Point d'entrée
│   │   ├── lib/
│   │   │   └── utils.ts     # Utilitaires (cn, etc.)
│   │   └── index.css        # Styles Tailwind
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
└── README.md
```

## 🔧 Configuration

### Backend

- **Modèle Whisper :** `base` (peut être changé en `small`, `medium`, `large` dans `main.py`)
- **Modèle Ollama :** `mistral` (peut être changé en `llama3` dans `main.py`)
- **Port :** `8000` (modifiable dans `main.py`)

### Frontend

- **URL API :** `http://localhost:8000` (modifiable dans `src/App.tsx`)
- **Port :** `5173` (par défaut avec Vite)

## 🐛 Dépannage

### Erreur "Ollama connection failed"

- Vérifiez qu'Ollama est bien installé et démarré
- Vérifiez que le modèle `mistral` est téléchargé : `ollama list`
- Si besoin, téléchargez le modèle : `ollama pull mistral`

### Erreur "FFmpeg not found"

- Vérifiez l'installation de FFmpeg : `ffmpeg -version`
- Assurez-vous que FFmpeg est dans votre PATH

### Erreur "Microphone access denied"

- Autorisez l'accès au microphone dans les paramètres de votre navigateur
- Utilisez HTTPS ou localhost (les navigateurs modernes exigent HTTPS pour l'accès microphone sauf sur localhost)

### Le backend ne démarre pas

- Vérifiez que le port 8000 n'est pas déjà utilisé
- Vérifiez que toutes les dépendances sont installées : `pip list`

### La transcription ne fonctionne pas

- Vérifiez que le fichier audio est bien envoyé (regardez les logs du backend)
- Vérifiez que Faster-Whisper est correctement installé
- Essayez avec un modèle plus petit si le CPU est lent : changez `"base"` en `"tiny"` dans `main.py`

## 📝 Notes Techniques

- **Souveraineté :** Tout le traitement se fait localement, aucune donnée n'est envoyée à des services externes
- **Performance :** Le modèle Whisper `base` est optimisé pour la vitesse tout en gardant une bonne précision
- **Format audio :** Le frontend enregistre en WebM/Opus, le backend le convertit automatiquement

## 🎨 Personnalisation

### Changer le modèle Whisper

Dans `backend/main.py`, ligne ~25 :
```python
whisper_model = WhisperModel("small", device=device, compute_type=compute_type)
```

### Changer le modèle Ollama

Dans `backend/main.py`, ligne ~95 :
```python
response = ollama.chat(
    model='llama3',  # Au lieu de 'mistral'
    ...
)
```

### Modifier le thème

Les couleurs sont définies dans `frontend/tailwind.config.js` et `frontend/src/index.css`

## 📄 Licence

Ce projet est une démonstration pour Lexia X.

---

**Développé avec ❤️ pour Lexia X**
