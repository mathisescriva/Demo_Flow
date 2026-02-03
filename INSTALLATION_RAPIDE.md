# 🚀 Installation Rapide - Lexia X Demo

## ✅ Ce qui est déjà installé

- ✅ **FFmpeg** : Installé
- ✅ **Python 3.9.13** : Installé
- ✅ **Node.js v25.2.0** : Installé
- ✅ **Dépendances Backend** : Installées dans `backend/venv/`
- ✅ **Dépendances Frontend** : Installées dans `frontend/node_modules/`

## ⚠️ Action requise : Installer Ollama

Ollama n'est **pas encore installé**. Vous devez l'installer manuellement :

### Installation d'Ollama

1. **Téléchargez Ollama** depuis [https://ollama.com](https://ollama.com)
2. **Installez-le** (glissez-déposez l'application dans Applications sur Mac)
3. **Téléchargez le modèle Mistral** :
   ```bash
   ollama run mistral
   ```
   (Cela téléchargera automatiquement le modèle ~4GB)

### Vérification

Une fois Ollama installé, vérifiez que le modèle est disponible :
```bash
ollama list
```

Vous devriez voir `mistral` dans la liste.

## 🎬 Démarrer la démo

### Terminal 1 - Backend
```bash
cd backend
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
uvicorn main:app --reload
```

Le backend sera accessible sur `http://localhost:8000`

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173`

## 🧪 Test rapide

1. Ouvrez `http://localhost:5173` dans votre navigateur
2. Autorisez l'accès au microphone
3. Cliquez sur "Démarrer l'enregistrement"
4. Dites : *"Hugo ici, j'ai une fuite sur la vanne V12, commande un kit de joint et mets l'alerte au max"*
5. Cliquez sur "Arrêter l'enregistrement"

Le système devrait extraire automatiquement :
- **Objet** : Vanne V12
- **Référence Pièce** : Kit de joint V12
- **Gravité** : 5/5
- **Action Requise** : Commander kit de joint et mettre alerte au maximum

## 📝 Notes

- Le premier démarrage de Whisper peut prendre quelques secondes (téléchargement du modèle)
- Assurez-vous qu'Ollama est démarré avant de lancer le backend
- Si vous avez des erreurs, consultez le README.md pour le dépannage
