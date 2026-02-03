# 🚀 Démarrage Rapide - Lexia X Demo

## ✅ Tout est installé et prêt !

Toutes les dépendances sont installées. Il ne reste plus qu'à démarrer les serveurs.

## 📋 Étapes de démarrage

### 1. Vérifier Ollama (si pas déjà fait)

Ouvrez un terminal et exécutez :
```bash
ollama list
```

Si vous ne voyez pas `mistral`, téléchargez-le :
```bash
ollama pull mistral
```

### 2. Démarrer le Backend

**Terminal 1 :**
```bash
cd /Users/mathisescriva/CascadeProjects/Demo_Flow
./start_backend.sh
```

Ou manuellement :
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

Le backend sera accessible sur **http://localhost:8000**

### 3. Démarrer le Frontend

**Terminal 2 :**
```bash
cd /Users/mathisescriva/CascadeProjects/Demo_Flow
./start_frontend.sh
```

Ou manuellement :
```bash
cd frontend
npm run dev
```

Le frontend sera accessible sur **http://localhost:5173**

### 4. Ouvrir dans le navigateur

Ouvrez **http://localhost:5173** dans votre navigateur.

## 🧪 Test de la démo

1. **Autorisez l'accès au microphone** lorsque le navigateur le demande
2. **Cliquez sur "Démarrer l'enregistrement"**
3. **Dites le message de test** :
   > "Hugo ici, j'ai une fuite sur la vanne V12, commande un kit de joint et mets l'alerte au max"
4. **Cliquez sur "Arrêter l'enregistrement"**

### Résultat attendu

La carte ERP devrait se remplir automatiquement avec :
- **Objet** : Vanne V12
- **Référence Pièce** : Kit de joint V12
- **Gravité** : 5/5 (Urgente)
- **Action Requise** : Commander kit de joint et mettre alerte au maximum

## 🔧 Scripts disponibles

- `./start_backend.sh` - Démarre le backend avec vérifications
- `./start_frontend.sh` - Démarre le frontend
- `./start_demo.sh` - Vérifie tout et donne les instructions
- `./check_setup.sh` - Vérifie l'état de l'installation

## ⚠️ Dépannage

### Ollama non trouvé
Si `ollama` n'est pas dans le PATH :
- Redémarrez votre terminal
- Ou ajoutez Ollama au PATH manuellement

### Le backend ne démarre pas
- Vérifiez que le port 8000 n'est pas utilisé
- Vérifiez que l'environnement virtuel est activé

### Le frontend ne démarre pas
- Vérifiez que le port 5173 n'est pas utilisé
- Vérifiez que `node_modules` est installé

### Erreur "Modèle non trouvé"
- Exécutez : `ollama pull mistral`
- Ou utilisez un autre modèle : `ollama pull llama3`

## 📝 Notes

- Le premier démarrage de Whisper peut prendre quelques secondes (téléchargement du modèle)
- Assurez-vous qu'Ollama est démarré avant d'utiliser l'endpoint `/action`
- La transcription fonctionne même sans Ollama, mais l'extraction d'action nécessite Ollama

---

**Tout est prêt ! Bonne démo ! 🎉**
