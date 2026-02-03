"""
Lexia X - Backend API
Démonstration End-to-End : Transcription locale + Intelligence locale
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import ollama
from faster_whisper import WhisperModel
import tempfile
import os
from typing import Optional, List
import json
import logging
from pydantic import BaseModel

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import re

def remove_repetitions(text: str) -> str:
    """
    Supprime les répétitions dans le texte transcrit.
    Ex: "qu'on a dit qu'on a dit qu'on a dit" -> "qu'on a dit"
    """
    if not text:
        return text
    
    # Chercher les patterns répétitifs (2-10 mots répétés 3+ fois)
    for pattern_len in range(2, 11):
        words = text.split()
        if len(words) < pattern_len * 3:
            continue
            
        # Chercher un pattern qui se répète
        for i in range(len(words) - pattern_len * 2):
            pattern = ' '.join(words[i:i+pattern_len])
            # Compter les occurrences consécutives
            count = 1
            pos = i + pattern_len
            while pos + pattern_len <= len(words):
                next_chunk = ' '.join(words[pos:pos+pattern_len])
                if next_chunk.lower().replace("'", "").replace("'", "") == pattern.lower().replace("'", "").replace("'", ""):
                    count += 1
                    pos += pattern_len
                else:
                    break
            
            # Si répété 3+ fois, garder une seule occurrence
            if count >= 3:
                logger.warning(f"Répétition détectée: '{pattern}' x{count}")
                # Reconstruire le texte sans répétitions
                before = ' '.join(words[:i+pattern_len])
                after = ' '.join(words[pos:])
                text = (before + ' ' + after).strip()
                # Recursively clean
                return remove_repetitions(text)
    
    return text

# Word Boost - Vocabulaire industriel par défaut
DEFAULT_VOCABULARY = [
    # Équipements
    "vanne", "pompe", "compresseur", "capteur", "moteur", "turbine",
    "V12", "V8", "P5", "P3", "C8", "S3", "M1", "T2",
    # Actions
    "fuite", "panne", "alerte", "maintenance", "remplacement", "inspection",
    # Pièces
    "joint", "roulement", "filtre", "courroie", "piston", "engrenage",
    # Priorités
    "urgent", "critique", "maximum", "immédiat", "prioritaire",
    # Personnes
    "Hugo", "Marie", "Pierre", "Jean", "Sophie",
]

# Vocabulaire personnalisé (modifiable via API)
custom_vocabulary: List[str] = []

app = FastAPI(title="Lexia X API", version="1.0.0")

# CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du modèle Whisper (modèle 'base' pour la vitesse)
# Utilise GPU si disponible, sinon CPU
device = "cuda" if os.getenv("USE_GPU", "false").lower() == "true" else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

logger.info(f"Initialisation de Whisper avec device={device}, compute_type={compute_type}")
whisper_model = WhisperModel("medium", device=device, compute_type=compute_type)

# Prompt système pour forcer le modèle à répondre en JSON
SYSTEM_PROMPT = """Tu es un assistant spécialisé dans l'extraction d'informations techniques depuis des messages vocaux en zone industrielle.

Tu dois TOUJOURS répondre UNIQUEMENT avec un JSON valide, sans texte avant ou après.

Le JSON doit contenir exactement ces champs :
- "objet" : Description courte de l'objet/équipement concerné (ex: "Vanne V12", "Pompe P5")
- "reference_piece" : Référence de la pièce ou du kit à commander (ex: "Kit de joint V12", "Roulement 6205")
- "gravite" : Niveau de gravité de 1 à 5 (1=faible, 5=critique/urgent)
- "action_requise" : Action à effectuer (ex: "Commander kit de joint", "Mettre alerte au maximum")

Exemples de réponses JSON valides :
{"objet": "Vanne V12", "reference_piece": "Kit de joint V12", "gravite": 5, "action_requise": "Commander kit de joint et mettre alerte au maximum"}
{"objet": "Pompe P5", "reference_piece": "Roulement 6205", "gravite": 3, "action_requise": "Planifier maintenance préventive"}

IMPORTANT : Réponds UNIQUEMENT avec le JSON, rien d'autre."""

@app.get("/")
async def root():
    return {"message": "Lexia X API - Backend de démonstration", "status": "ready"}

@app.get("/health")
async def health():
    """Vérifie que le backend est opérationnel"""
    return {
        "status": "healthy",
        "whisper": "ready",
        "ollama": "ready"
    }

# ============== WORD BOOST ==============

class VocabularyUpdate(BaseModel):
    words: List[str]

@app.get("/vocabulary")
async def get_vocabulary():
    """Récupère le vocabulaire actuel (par défaut + personnalisé)"""
    all_words = list(set(DEFAULT_VOCABULARY + custom_vocabulary))
    return {
        "default": DEFAULT_VOCABULARY,
        "custom": custom_vocabulary,
        "all": all_words,
        "total": len(all_words)
    }

@app.post("/vocabulary")
async def update_vocabulary(update: VocabularyUpdate):
    """Met à jour le vocabulaire personnalisé"""
    global custom_vocabulary
    custom_vocabulary = list(set(update.words))  # Dédupliquer
    logger.info(f"Vocabulaire mis à jour: {len(custom_vocabulary)} mots personnalisés")
    return {
        "success": True,
        "custom": custom_vocabulary,
        "total": len(set(DEFAULT_VOCABULARY + custom_vocabulary))
    }

@app.post("/vocabulary/add")
async def add_vocabulary_word(word: str = Body(..., embed=True)):
    """Ajoute un mot au vocabulaire personnalisé"""
    global custom_vocabulary
    if word and word not in custom_vocabulary and word not in DEFAULT_VOCABULARY:
        custom_vocabulary.append(word)
        logger.info(f"Mot ajouté au vocabulaire: {word}")
    return {
        "success": True,
        "word": word,
        "custom": custom_vocabulary
    }

def get_word_boost_prompt(extra_words: list = None):
    """Génère le prompt de boost pour Whisper"""
    all_words = list(set(DEFAULT_VOCABULARY + custom_vocabulary + (extra_words or [])))
    if not all_words:
        return None
    # Whisper utilise initial_prompt pour biaiser vers certains mots
    return f"Vocabulaire technique: {', '.join(all_words[:50])}."  # Limité à 50 mots

# ============== END WORD BOOST ==============

@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    word_boost_words: Optional[str] = Form(None)
):
    """
    Endpoint pour transcrire un fichier audio en texte.
    Reçoit un fichier audio (WAV, MP3, etc.) et renvoie la transcription.
    word_boost_words: mots séparés par des virgules pour améliorer leur reconnaissance
    """
    try:
        # Parser les mots Word Boost
        extra_words = []
        if word_boost_words:
            extra_words = [w.strip() for w in word_boost_words.split(',') if w.strip()]
            logger.info(f"Word Boost personnalisé: {extra_words}")
        
        logger.info(f"Reçu fichier audio: {audio.filename}, type: {audio.content_type}")
        
        # Sauvegarder temporairement le fichier audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Transcription avec Whisper + Word Boost
            logger.info("Début de la transcription...")
            word_boost = get_word_boost_prompt(extra_words)
            boosted_words = [w.lower() for w in (DEFAULT_VOCABULARY + custom_vocabulary + extra_words)]
            logger.info(f"Word Boost activé ({len(boosted_words)} mots): {word_boost[:80] if word_boost else 'Non'}...")
            
            segments, info = whisper_model.transcribe(
                tmp_path, 
                beam_size=5,
                initial_prompt=word_boost,  # Word Boost!
                language="fr",  # Force le français
                vad_filter=False,  # DÉSACTIVÉ - le VAD filtrait tout l'audio!
                word_timestamps=True,  # Timestamps par mot pour la confiance
                condition_on_previous_text=False,  # Évite les répétitions!
                compression_ratio_threshold=2.4,  # Plus permissif
                log_prob_threshold=-1.0,  # Plus permissif
                no_speech_threshold=0.6,  # Plus permissif
                temperature=0.0,  # Déterministe, moins d'hallucinations
            )
            
            # Récupérer les mots avec leur confiance
            words_with_confidence = []
            full_text = ""
            seen_segments = set()
            
            for segment in segments:
                # Filtrer les segments répétitifs ou hallucinés
                segment_text = segment.text.strip()
                
                # Ignorer les segments vides ou trop courts
                if len(segment_text) < 3:
                    continue
                    
                # Ignorer les segments qui se répètent
                segment_key = segment_text[:30].lower()
                if segment_key in seen_segments:
                    logger.warning(f"Segment répétitif ignoré: {segment_text[:50]}")
                    continue
                seen_segments.add(segment_key)
                
                # Ignorer les hallucinations typiques
                hallucination_patterns = [
                    "je vous invite", "merci d'avoir", "n'oubliez pas", 
                    "abonnez", "likez", "nouvelle vidéo", "à bientôt",
                    "sous-titres", "transcription", "l'écrité"
                ]
                is_hallucination = any(p in segment_text.lower() for p in hallucination_patterns)
                if is_hallucination:
                    logger.warning(f"Hallucination détectée et ignorée: {segment_text[:50]}")
                    continue
                
                full_text += segment.text
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        word_text = word.word.strip()
                        # Vérifier si le mot est dans le vocabulaire boosté
                        is_boosted = any(
                            boost_word in word_text.lower() 
                            for boost_word in boosted_words
                        )
                        words_with_confidence.append({
                            "word": word_text,
                            "confidence": word.probability if hasattr(word, 'probability') else 0.9,
                            "start": word.start,
                            "end": word.end,
                            "boosted": is_boosted
                        })
            
            # Post-traitement: supprimer les répétitions dans le texte
            clean_text = remove_repetitions(full_text.strip())
            
            logger.info(f"Transcription réussie: {clean_text[:100]}...")
            
            return {
                "text": clean_text,
                "words": words_with_confidence,
                "language": info.language,
                "language_probability": info.language_probability
            }
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Erreur lors de la transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de transcription: {str(e)}")

@app.post("/reformat")
async def reformat_text(data: dict):
    """
    Endpoint pour reformater le texte dicté.
    CONSERVATEUR: ne formate en mail/liste que si EXPLICITEMENT demandé.
    Utilise le Word Boost comme contexte pour le LLM.
    """
    try:
        raw_text = data.get("text", "").strip()
        word_boost_words = data.get("word_boost_words", [])
        
        if not raw_text:
            return {"formatted": "", "type": "unknown"}
        
        logger.info(f"Reformatage de: {raw_text[:50]}...")
        
        # Construire le contexte Word Boost pour le LLM
        word_boost_context = ""
        all_boost_words = list(set(DEFAULT_VOCABULARY + custom_vocabulary + word_boost_words))
        if all_boost_words:
            word_boost_context = f"""
CONTEXTE IMPORTANT - Vocabulaire technique à respecter:
Ces mots sont des termes techniques, noms propres ou références spécifiques. 
Conserve leur orthographe exacte: {', '.join(all_boost_words[:30])}
"""
            logger.info(f"Word Boost contexte LLM: {len(all_boost_words)} mots")
        
        # Détection EXPLICITE du type demandé
        lower_text = raw_text.lower()
        is_email_request = any(kw in lower_text for kw in ["écris un mail", "envoie un mail", "mail à", "email à", "écris un email", "envoie un email"])
        is_list_request = any(kw in lower_text for kw in ["liste de", "rappelle-moi", "rappelle moi", "acheter", "à faire", "todo"])
        
        if is_email_request:
            prompt = f"""{word_boost_context}
Transforme cette dictée en email professionnel bien formaté.
Ajoute: Objet, Salutation, Corps structuré, Formule de politesse.
Ne garde PAS les instructions ("écris un mail à..."), juste le contenu.

Dictée: {raw_text}

Email:"""
            text_type = "email"
        elif is_list_request:
            prompt = f"""{word_boost_context}
Transforme cette dictée en liste claire avec tirets.
Garde uniquement les éléments, pas les instructions.

Dictée: {raw_text}

Liste:"""
            text_type = "list"
        else:
            # PAR DÉFAUT: juste nettoyer la ponctuation, garder le texte tel quel
            prompt = f"""{word_boost_context}
Corrige UNIQUEMENT la ponctuation et les fautes de ce texte dicté.
NE CHANGE PAS le style, NE RAJOUTE RIEN, garde exactement le même contenu.
IMPORTANT: Respecte l'orthographe exacte des termes techniques du contexte.
Pas de guillemets autour.

Texte: {raw_text}

Texte corrigé:"""
            text_type = "text"

        response = ollama.chat(
            model="qwen2.5:7b-instruct",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1, "num_predict": 500}
        )
        
        formatted = response["message"]["content"].strip()
        
        # Nettoyer les guillemets si présents
        if formatted.startswith('"') and formatted.endswith('"'):
            formatted = formatted[1:-1]
        if formatted.startswith("'") and formatted.endswith("'"):
            formatted = formatted[1:-1]
        
        logger.info(f"Reformaté ({text_type}): {formatted[:50]}...")
        
        return {
            "formatted": formatted,
            "type": text_type,
            "original": raw_text
        }
        
    except Exception as e:
        logger.error(f"Erreur reformatage: {str(e)}")
        return {
            "formatted": data.get("text", ""),
            "type": "raw",
            "error": str(e)
        }

@app.post("/action")
async def extract_action(text: dict):
    """
    Endpoint pour extraire les informations structurées depuis le texte transcrit.
    Utilise Ollama avec un modèle local pour générer le JSON structuré.
    """
    try:
        if "text" not in text:
            raise HTTPException(status_code=400, detail="Le champ 'text' est requis")
        
        user_text = text["text"]
        logger.info(f"Extraction d'action depuis: {user_text[:100]}...")
        
        # Construction du prompt utilisateur
        user_prompt = f"Extrait les informations depuis ce message vocal industriel:\n\n{user_text}"
        
        # Appel à Ollama avec le modèle Mistral (ou Llama3 si disponible)
        try:
            # Vérifier que le modèle est disponible
            try:
                response = ollama.chat(
                    model='qwen2.5:7b-instruct',
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            except Exception as model_error:
                # Si mistral n'est pas disponible, essayer llama3
                if 'mistral' in str(model_error).lower() or 'not found' in str(model_error).lower():
                    logger.warning("Modèle mistral non trouvé, tentative avec llama3...")
                    try:
                        response = ollama.chat(
                            model='mistral',  # Fallback
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt}
                            ]
                        )
                    except:
                        raise model_error
                else:
                    raise
            
            # Récupérer la réponse
            llm_response = response['message']['content'].strip()
            logger.info(f"Réponse LLM brute: {llm_response}")
            
            # Parser le JSON (parfois le modèle ajoute du texte, on extrait juste le JSON)
            # Chercher le JSON dans la réponse
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("Aucun JSON trouvé dans la réponse du modèle")
            
            json_str = llm_response[json_start:json_end]
            parsed_json = json.loads(json_str)
            
            # Validation des champs requis
            required_fields = ["objet", "reference_piece", "gravite", "action_requise"]
            for field in required_fields:
                if field not in parsed_json:
                    raise ValueError(f"Champ manquant: {field}")
            
            # S'assurer que gravite est un entier entre 1 et 5
            parsed_json["gravite"] = int(parsed_json["gravite"])
            if not (1 <= parsed_json["gravite"] <= 5):
                parsed_json["gravite"] = max(1, min(5, parsed_json["gravite"]))
            
            logger.info(f"JSON extrait avec succès: {parsed_json}")
            
            return {
                "success": True,
                "data": parsed_json,
                "original_text": user_text
            }
            
        except Exception as ollama_error:
            logger.error(f"Erreur Ollama: {str(ollama_error)}")
            # Fallback : retourner une structure par défaut si Ollama échoue
            return {
                "success": False,
                "error": f"Erreur Ollama: {str(ollama_error)}",
                "data": {
                    "objet": "Non déterminé",
                    "reference_piece": "Non déterminé",
                    "gravite": 1,
                    "action_requise": "Vérification manuelle requise"
                },
                "original_text": user_text
            }
            
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur d'extraction: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
