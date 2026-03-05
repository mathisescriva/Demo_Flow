"""
Lexia X - Backend API
Démonstration End-to-End : Transcription + Intelligence via Mistral API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import tempfile
import os
from typing import Optional, List
import json
import logging
from pydantic import BaseModel
from datetime import datetime
from collections import deque
from dotenv import load_dotenv
import httpx

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

# ============== DASHBOARD DATA ==============
dashboard_tickets: List[dict] = []
dashboard_logs: deque = deque(maxlen=100)

def add_log(level: str, source: str, message: str):
    """Ajoute un log au dashboard."""
    dashboard_logs.appendleft({
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "source": source,
        "message": message
    })

app = FastAPI(title="Lexia X API", version="1.0.0")

# CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
VOXTRAL_URL = "https://api.mistral.ai/v1/audio/transcriptions"

MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_LLM_MODEL = "mistral-small-latest"

if MISTRAL_API_KEY:
    logger.info("Clé Mistral détectée - Voxtral v2 + LLM prêts")
else:
    logger.warning("MISTRAL_API_KEY non trouvée - services Mistral indisponibles")


async def mistral_chat(messages: list, temperature: float = 0.1, max_tokens: int = 500) -> str:
    """Appelle le LLM Mistral via API HTTP."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            MISTRAL_CHAT_URL,
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MISTRAL_LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
    if response.status_code != 200:
        raise RuntimeError(f"Mistral LLM erreur {response.status_code}: {response.text[:200]}")
    return response.json()["choices"][0]["message"]["content"].strip()

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
        "stt": "voxtral" if MISTRAL_API_KEY else "unavailable",
        "llm": "mistral" if MISTRAL_API_KEY else "unavailable"
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

def get_context_bias(extra_words: list = None) -> List[str]:
    """Retourne la liste de termes pour le context biasing Voxtral (max 100, mots simples sans espaces)."""
    raw = DEFAULT_VOCABULARY + custom_vocabulary + (extra_words or [])
    # Voxtral exige des tokens sans espaces ni virgules
    tokens = set()
    for term in raw:
        for word in term.split():
            cleaned = word.strip(",;:!?.")
            if cleaned:
                tokens.add(cleaned)
    return list(tokens)[:100]

# ============== END WORD BOOST ==============

@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    word_boost_words: Optional[str] = Form(None)
):
    """
    Transcrit un fichier audio via Voxtral v2 API (Mistral).
    word_boost_words: mots séparés par des virgules pour le context biasing
    """
    if not MISTRAL_API_KEY:
        raise HTTPException(status_code=503, detail="MISTRAL_API_KEY non configurée")

    try:
        extra_words = []
        if word_boost_words:
            extra_words = [w.strip() for w in word_boost_words.split(',') if w.strip()]
            logger.info(f"Context bias personnalisé: {extra_words}")

        logger.info(f"Reçu fichier audio: {audio.filename}, type: {audio.content_type}")
        add_log("INFO", "SPEECH-TO-TEXT", f"Flux audio reçu ({audio.content_type})")

        suffix = ".webm" if audio.content_type and "webm" in audio.content_type else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            logger.info("Transcription via Voxtral v2...")
            context_bias = get_context_bias(extra_words)
            logger.info(f"Context bias: {len(context_bias)} termes")
            add_log("INFO", "VOXTRAL", f"Context bias: {len(context_bias)} termes actifs")

            with open(tmp_path, "rb") as audio_file:
                fields = [
                    ("model", (None, "voxtral-mini-latest")),
                    ("language", (None, "fr")),
                    ("timestamp_granularities", (None, "word")),
                    ("file", (f"recording{suffix}", audio_file, audio.content_type or "audio/webm")),
                ]
                for term in context_bias:
                    fields.append(("context_bias", (None, term)))

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        VOXTRAL_URL,
                        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                        files=fields,
                    )

            if response.status_code != 200:
                error_detail = response.text[:200]
                logger.error(f"Voxtral API erreur {response.status_code}: {error_detail}")
                raise HTTPException(status_code=502, detail=f"Voxtral API erreur: {error_detail}")

            result = response.json()
            logger.info(f"Voxtral segments: {len(result.get('segments', []))}, keys: {list(result.keys())}")
            if result.get("segments"):
                seg0 = result["segments"][0]
                logger.info(f"Segment[0] keys: {list(seg0.keys())}, words: {len(seg0.get('words', []))}")
            full_text = result.get("text", "")
            clean_text = remove_repetitions(full_text.strip())

            words_with_confidence = []
            bias_set = {w.lower() for w in context_bias}

            has_words = False
            for segment in result.get("segments", []):
                for word in segment.get("words", []):
                    has_words = True
                    word_text = word.get("text", "").strip()
                    if not word_text:
                        continue
                    words_with_confidence.append({
                        "word": word_text,
                        "confidence": word.get("confidence", 0.95),
                        "start": word.get("start", 0),
                        "end": word.get("end", 0),
                        "boosted": word_text.lower() in bias_set
                    })

            if not has_words and clean_text:
                for w in clean_text.split():
                    words_with_confidence.append({
                        "word": w,
                        "confidence": 0.95,
                        "start": 0,
                        "end": 0,
                        "boosted": w.lower().strip(".,;:!?") in bias_set
                    })

            logger.info(f"Transcription Voxtral réussie: {clean_text[:100]}...")
            add_log("OK", "SPEECH-TO-TEXT", f"Transcription: {clean_text[:80]}")

            return {
                "text": clean_text,
                "words": words_with_confidence,
                "language": result.get("language", "fr"),
                "language_probability": 0.99
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la transcription Voxtral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de transcription: {str(e)}")

@app.post("/reformat")
async def reformat_text(data: dict):
    """
    Endpoint pour reformater le texte dicté.
    CONSERVATEUR: ne formate en mail/liste que si EXPLICITEMENT demandé.
    """
    try:
        raw_text = data.get("text", "").strip()
        
        if not raw_text:
            return {"formatted": "", "type": "unknown"}
        
        logger.info(f"Reformatage de: {raw_text[:50]}...")
        
        # Détection EXPLICITE du type demandé
        lower_text = raw_text.lower()
        is_email_request = any(kw in lower_text for kw in ["écris un mail", "envoie un mail", "mail à", "email à", "écris un email", "envoie un email"])
        is_list_request = any(kw in lower_text for kw in ["liste de", "rappelle-moi", "rappelle moi", "acheter", "à faire", "todo"])
        
        if is_email_request:
            prompt = f"""Transforme cette dictée en email professionnel bien formaté.
Ajoute: Objet, Salutation, Corps structuré, Formule de politesse.
Ne garde PAS les instructions ("écris un mail à..."), juste le contenu.

Dictée: {raw_text}

Email:"""
            text_type = "email"
        elif is_list_request:
            prompt = f"""Transforme cette dictée en liste claire avec tirets.
Garde uniquement les éléments, pas les instructions.

Dictée: {raw_text}

Liste:"""
            text_type = "list"
        else:
            # PAR DÉFAUT: juste nettoyer la ponctuation, garder le texte tel quel
            prompt = f"""Corrige UNIQUEMENT la ponctuation et les fautes de ce texte dicté.
NE CHANGE PAS le style, NE RAJOUTE RIEN, garde exactement le même contenu.
Pas de guillemets autour.

Texte: {raw_text}

Texte corrigé:"""
            text_type = "text"

        formatted = await mistral_chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        
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
    Utilise Mistral API pour générer le JSON structuré.
    """
    try:
        if "text" not in text:
            raise HTTPException(status_code=400, detail="Le champ 'text' est requis")
        
        user_text = text["text"]
        logger.info(f"Extraction d'action depuis: {user_text[:100]}...")
        add_log("INFO", "AI-ENGINE", f"Extraction de données structurées en cours...")
        
        # Construction du prompt utilisateur
        user_prompt = f"Extrait les informations depuis ce message vocal industriel:\n\n{user_text}"
        
        try:
            llm_response = await mistral_chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=500,
            )
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
            
            # Stocker le ticket pour le dashboard
            ticket_id = f"TKT-{datetime.now().strftime('%H%M%S')}"
            ticket = {
                "id": ticket_id,
                "objet": parsed_json["objet"],
                "reference": parsed_json["reference_piece"],
                "gravite": parsed_json["gravite"],
                "action": parsed_json["action_requise"],
                "original": user_text,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "Nouveau"
            }
            dashboard_tickets.insert(0, ticket)
            add_log("OK", "AI-ENGINE", f"Données extraites: {parsed_json['objet']}")
            add_log("OK", "ERP-CONNECTOR", f"Notification créée [{ticket_id}] — Gravité {parsed_json['gravite']}/5")
            add_log("INFO", "ERP-CONNECTOR", f"Action: {parsed_json['action_requise'][:60]}")
            
            return {
                "success": True,
                "data": parsed_json,
                "original_text": user_text
            }
            
        except Exception as llm_error:
            logger.error(f"Erreur LLM Mistral: {str(llm_error)}")
            return {
                "success": False,
                "error": f"Erreur LLM: {str(llm_error)}",
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

# ============== DASHBOARD SAP ==============

@app.get("/dashboard/tickets")
async def get_dashboard_tickets():
    return dashboard_tickets

@app.get("/dashboard/logs")
async def get_dashboard_logs():
    return list(dashboard_logs)

@app.get("/dashboard/clear")
async def clear_dashboard():
    dashboard_tickets.clear()
    dashboard_logs.clear()
    add_log("INFO", "SYSTEM", "Dashboard réinitialisé")
    return {"success": True}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SAP S/4HANA — Maintenance Notifications</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
@keyframes rowIn{from{opacity:0;background:rgba(0,112,192,.08)}to{opacity:1;background:transparent}}
body{
  font-family:'72','72full',Arial,Helvetica,sans-serif;
  background:#fafafa;color:#32363a;font-size:13px;height:100vh;overflow:hidden;
  display:flex;flex-direction:column;
}
/* SAP Shell Bar */
.sap-shell{
  background:#354a5f;height:44px;display:flex;align-items:center;
  padding:0 16px;color:#fff;flex-shrink:0;
}
.sap-shell-logo{font-size:15px;font-weight:700;letter-spacing:.3px;margin-right:24px;display:flex;align-items:center;gap:8px}
.sap-shell-logo svg{width:42px;height:18px}
.sap-shell-nav{display:flex;gap:0;flex:1}
.sap-shell-item{
  padding:10px 16px;font-size:13px;color:rgba(255,255,255,.8);cursor:pointer;
  border-bottom:2px solid transparent;
}
.sap-shell-item:hover{color:#fff;background:rgba(255,255,255,.06)}
.sap-shell-item.active{color:#fff;border-bottom:2px solid #d1e8ff}
.sap-shell-right{display:flex;align-items:center;gap:12px}
.sap-shell-right .sap-icon{
  width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  cursor:pointer;color:rgba(255,255,255,.7);font-size:14px;
}
.sap-shell-right .sap-icon:hover{background:rgba(255,255,255,.1);color:#fff}
.sap-avatar{
  width:32px;height:32px;border-radius:50%;background:#6c8ebf;
  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:#fff;
}
/* Sub-header */
.sap-subheader{
  background:#fff;border-bottom:1px solid #d9d9d9;
  padding:12px 24px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;
}
.sap-page-title{font-size:20px;font-weight:400;color:#32363a}
.sap-kpis{display:flex;gap:24px}
.sap-kpi{text-align:center}
.sap-kpi-val{font-size:28px;font-weight:300;color:#0070c0}
.sap-kpi-label{font-size:11px;color:#6a6d70;margin-top:2px}
/* Filter bar */
.sap-filter{
  background:#fff;border-bottom:1px solid #ededed;
  padding:8px 24px;display:flex;align-items:center;gap:12px;flex-shrink:0;
}
.sap-filter-btn{
  padding:6px 12px;border:1px solid #bfbfbf;border-radius:4px;
  background:#fff;font-size:12px;color:#32363a;cursor:pointer;
  font-family:inherit;
}
.sap-filter-btn:hover{background:#f2f2f2}
.sap-filter-btn.active{background:#0070c0;color:#fff;border-color:#0070c0}
.sap-filter-input{
  padding:6px 10px;border:1px solid #bfbfbf;border-radius:4px;
  font-size:12px;width:200px;font-family:inherit;
}
.sap-filter-sep{width:1px;height:24px;background:#e5e5e5}
.sap-filter-right{margin-left:auto;display:flex;align-items:center;gap:8px}
.sap-count{font-size:12px;color:#6a6d70}
/* Table */
.sap-table-wrap{flex:1;overflow-y:auto;background:#fafafa;padding:0}
table{width:100%;border-collapse:collapse;background:#fff}
thead{position:sticky;top:0;z-index:2}
th{
  background:#f2f2f2;border-bottom:1px solid #d9d9d9;
  padding:10px 14px;text-align:left;font-weight:600;font-size:12px;
  color:#6a6d70;text-transform:none;white-space:nowrap;
}
td{
  padding:10px 14px;border-bottom:1px solid #ededed;font-size:13px;
  color:#32363a;vertical-align:middle;
}
tr{animation:rowIn .4s ease}
tr:hover{background:#f5f8fc}
.td-id{font-weight:600;color:#0070c0;cursor:pointer}
.td-id:hover{text-decoration:underline}
.priority-indicator{
  display:inline-flex;align-items:center;gap:6px;
}
.priority-dot{width:10px;height:10px;border-radius:2px;flex-shrink:0}
.p-critical{background:#bb0000}
.p-high{background:#e78c07}
.p-medium{background:#2b7d2b}
.p-low{background:#5899da}
.sap-status{
  padding:3px 8px;border-radius:3px;font-size:11px;font-weight:600;
  display:inline-block;
}
.st-new{background:#fff3b8;color:#8a6d00;border:1px solid #e8d57a}
.st-progress{background:#d4edda;color:#155724;border:1px solid #a8d5b8}
.empty-table{
  padding:60px;text-align:center;color:#ababab;font-size:14px;
}
.empty-table svg{margin-bottom:12px;opacity:.3}
/* Notification bell badge */
.notif-badge{
  position:absolute;top:-2px;right:-2px;width:16px;height:16px;
  background:#bb0000;border-radius:50%;font-size:9px;color:#fff;
  display:flex;align-items:center;justify-content:center;font-weight:700;
}
</style>
</head>
<body>
<!-- SAP Shell Bar -->
<div class="sap-shell">
  <div class="sap-shell-logo">
    <svg viewBox="0 0 92 40" fill="none"><text x="0" y="28" font-family="Arial" font-weight="700" font-size="26" fill="#fff">SAP</text></svg>
  </div>
  <div class="sap-shell-nav">
    <div class="sap-shell-item">Accueil</div>
    <div class="sap-shell-item active">Notifications de maintenance</div>
    <div class="sap-shell-item">Ordres de travail</div>
    <div class="sap-shell-item">Équipements</div>
  </div>
  <div class="sap-shell-right">
    <div class="sap-icon" style="position:relative">🔔<span class="notif-badge" id="bell-badge" style="display:none">0</span></div>
    <div class="sap-icon">⚙</div>
    <div class="sap-avatar">ME</div>
  </div>
</div>

<!-- Sub-header -->
<div class="sap-subheader">
  <div class="sap-page-title">Notifications de maintenance</div>
  <div class="sap-kpis">
    <div class="sap-kpi">
      <div class="sap-kpi-val" id="kpi-total">0</div>
      <div class="sap-kpi-label">Total</div>
    </div>
    <div class="sap-kpi">
      <div class="sap-kpi-val" id="kpi-critical" style="color:#bb0000">0</div>
      <div class="sap-kpi-label">Très élevée</div>
    </div>
    <div class="sap-kpi">
      <div class="sap-kpi-val" id="kpi-open" style="color:#e78c07">0</div>
      <div class="sap-kpi-label">En cours</div>
    </div>
  </div>
</div>

<!-- Filter bar -->
<div class="sap-filter">
  <button class="sap-filter-btn active">Toutes</button>
  <button class="sap-filter-btn">Ouvertes</button>
  <button class="sap-filter-btn">En traitement</button>
  <button class="sap-filter-btn">Clôturées</button>
  <div class="sap-filter-sep"></div>
  <input class="sap-filter-input" placeholder="Rechercher une notification..." />
  <div class="sap-filter-right">
    <span class="sap-count" id="table-count">0 notifications</span>
  </div>
</div>

<!-- Table -->
<div class="sap-table-wrap">
  <table>
    <thead>
      <tr>
        <th style="width:110px">Notification</th>
        <th>Type notif.</th>
        <th>Description</th>
        <th>Poste technique</th>
        <th style="width:100px">Priorité</th>
        <th>Action requise</th>
        <th style="width:90px">Statut</th>
        <th style="width:70px">Heure</th>
      </tr>
    </thead>
    <tbody id="table-body">
      <tr>
        <td colspan="8" class="empty-table">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6m-6 4h4"/></svg>
          <div>Aucune notification. En attente de saisie vocale...</div>
        </td>
      </tr>
    </tbody>
  </table>
</div>

<script>
let lastCount = 0;

function priorityLabel(g) {
  if (g >= 5) return {text:'Très élevée', cls:'p-critical'};
  if (g >= 4) return {text:'Élevée', cls:'p-high'};
  if (g >= 3) return {text:'Moyenne', cls:'p-medium'};
  return {text:'Faible', cls:'p-low'};
}

function notifType(g) {
  if (g >= 4) return 'M2 - Urgent';
  if (g >= 3) return 'M1 - Maintenance';
  return 'M3 - Observation';
}

function renderRow(t) {
  const p = priorityLabel(t.gravite);
  return `<tr>
    <td class="td-id">${t.id}</td>
    <td>${notifType(t.gravite)}</td>
    <td style="font-weight:500">${t.objet}</td>
    <td>${t.reference}</td>
    <td><div class="priority-indicator"><div class="priority-dot ${p.cls}"></div>${p.text}</div></td>
    <td style="color:#6a6d70">${t.action}</td>
    <td><span class="sap-status st-new">Ouverte</span></td>
    <td style="color:#ababab">${t.timestamp}</td>
  </tr>`;
}

async function refresh() {
  try {
    const res = await fetch('/dashboard/tickets');
    const tickets = await res.json();

    document.getElementById('kpi-total').textContent = tickets.length;
    document.getElementById('kpi-critical').textContent = tickets.filter(t => t.gravite >= 4).length;
    document.getElementById('kpi-open').textContent = tickets.length;
    document.getElementById('table-count').textContent = tickets.length + ' notification' + (tickets.length > 1 ? 's' : '');

    if (tickets.length > 0) {
      const badge = document.getElementById('bell-badge');
      badge.style.display = 'flex';
      badge.textContent = tickets.length;
    }

    if (tickets.length !== lastCount) {
      if (tickets.length > 0) {
        document.getElementById('table-body').innerHTML = tickets.map(renderRow).join('');
      }
      lastCount = tickets.length;
    }
  } catch(e) {}
}

setInterval(refresh, 500);
refresh();
</script>
</body>
</html>"""


@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>System Logs</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
@keyframes lineIn{from{opacity:0}to{opacity:1}}
body{
  font-family:'SF Mono','Fira Code','Cascadia Code',monospace;
  background:#0c0c0c;color:#a0a0a0;font-size:12px;height:100vh;overflow:hidden;
  display:flex;flex-direction:column;
}
.header{
  background:#111;border-bottom:1px solid #1a1a1a;
  padding:10px 16px;display:flex;align-items:center;justify-content:space-between;
  flex-shrink:0;
}
.header-title{font-size:12px;color:#555;font-weight:600;letter-spacing:1px;text-transform:uppercase}
.header-stats{display:flex;gap:16px;font-size:11px}
.header-stats span{color:#444}
.header-stats .val{color:#888}
.dot{display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:4px}
.dot-green{background:#22c55e}
.log-wrap{flex:1;overflow-y:auto;padding:8px 0}
.log-line{
  padding:3px 16px;display:flex;gap:0;white-space:nowrap;
  animation:lineIn .15s ease;line-height:1.7;
}
.log-line:hover{background:#111}
.l-time{color:#333;width:72px;flex-shrink:0}
.l-level{width:14px;flex-shrink:0;text-align:center}
.l-ok{color:#22c55e}
.l-info{color:#3b82f6}
.l-warn{color:#f59e0b}
.l-err{color:#ef4444}
.l-source{color:#555;width:120px;flex-shrink:0;font-weight:600;font-size:11px}
.l-sep{color:#1a1a1a;margin:0 8px;flex-shrink:0}
.l-msg{color:#666;overflow:hidden;text-overflow:ellipsis}
.footer{
  background:#111;border-top:1px solid #1a1a1a;
  padding:6px 16px;font-size:11px;color:#333;flex-shrink:0;
  display:flex;align-items:center;gap:8px;
}
</style>
</head>
<body>
<div class="header">
  <div class="header-title"><span class="dot dot-green"></span> System Logs</div>
  <div class="header-stats">
    <span>events: <span class="val" id="s-total">0</span></span>
    <span>uptime: <span class="val" id="s-uptime">0s</span></span>
  </div>
</div>
<div class="log-wrap" id="log-wrap"></div>
<div class="footer">
  <span class="dot dot-green"></span> connected — polling 500ms
</div>
<script>
let lastCount = 0;
const start = Date.now();

function renderLine(l) {
  const lc = l.level === 'OK' ? 'l-ok' : l.level === 'WARN' ? 'l-warn' : l.level === 'ERR' ? 'l-err' : 'l-info';
  const sym = l.level === 'OK' ? '✓' : l.level === 'ERR' ? '✗' : l.level === 'WARN' ? '!' : '·';
  return `<div class="log-line"><span class="l-time">${l.time}</span><span class="l-level ${lc}">${sym}</span><span class="l-source">${l.source}</span><span class="l-sep">│</span><span class="l-msg">${l.message}</span></div>`;
}

async function refresh() {
  try {
    const res = await fetch('/dashboard/logs');
    const logs = await res.json();
    document.getElementById('s-total').textContent = logs.length;
    const sec = Math.floor((Date.now() - start) / 1000);
    const m = Math.floor(sec/60);
    document.getElementById('s-uptime').textContent = m > 0 ? m+'m'+sec%60+'s' : sec+'s';
    if (logs.length !== lastCount) {
      document.getElementById('log-wrap').innerHTML = logs.map(renderLine).join('');
      lastCount = logs.length;
    }
  } catch(e) {}
}

setInterval(refresh, 500);
refresh();
</script>
</body>
</html>"""


@app.get("/showcase/logo")
async def showcase_logo():
    """Serve the Lexia logo for the showcase page."""
    import base64
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'logo_lexia.webp')
    if os.path.exists(logo_path):
        from fastapi.responses import Response
        with open(logo_path, 'rb') as f:
            return Response(content=f.read(), media_type="image/webp")
    return Response(content=b"", media_type="image/webp")

@app.get("/showcase", response_class=HTMLResponse)
async def showcase_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Lexia — Voice to Action</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  background:#f0f2f5;color:#1d1d1f;height:100vh;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
  -webkit-font-smoothing:antialiased;
  position:relative;
}
/* Subtle mesh gradient background */
body::before{
  content:'';position:absolute;inset:0;
  background:
    radial-gradient(ellipse 80% 60% at 20% 30%, rgba(59,130,246,.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 70%, rgba(168,85,247,.05) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 50% 10%, rgba(34,197,94,.04) 0%, transparent 50%);
  pointer-events:none;
}
/* Dot pattern overlay */
body::after{
  content:'';position:absolute;inset:0;
  background-image:radial-gradient(circle,rgba(0,0,0,.03) 1px,transparent 1px);
  background-size:20px 20px;pointer-events:none;
}

.scene{width:1340px;height:800px;position:relative;display:flex;gap:0;z-index:1}

/* ============ DASHBOARD ============ */
.dashboard{
  flex:1;background:rgba(255,255,255,.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-radius:20px 0 0 20px;
  border:1px solid rgba(255,255,255,.6);overflow:hidden;display:flex;
  box-shadow:0 25px 80px rgba(0,0,0,.06),0 8px 32px rgba(0,0,0,.04),0 0 0 1px rgba(0,0,0,.03);
}
.side{
  width:230px;background:rgba(250,250,250,.9);border-right:1px solid #e8e8ea;
  padding:22px 14px;display:flex;flex-direction:column;
}
.side-logo{display:flex;align-items:center;gap:10px;margin-bottom:30px;padding:0 8px}
.side-logo img{height:24px;width:auto}
.side-section{font-size:9.5px;color:#aaa;text-transform:uppercase;letter-spacing:1px;margin:22px 0 8px;padding:0 10px;font-weight:600}
.side-item{
  padding:10px 12px;border-radius:10px;font-size:13px;color:#888;
  display:flex;align-items:center;gap:10px;margin-bottom:2px;cursor:default;
  transition:all .15s ease;
}
.side-item.active{background:#fff;color:#1d1d1f;font-weight:500;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.side-item svg{width:16px;height:16px;opacity:.45}
.side-item.active svg{opacity:.7}
.side-item .badge{margin-left:auto;font-size:10px;background:#ef4444;color:#fff;padding:2px 7px;border-radius:8px;font-weight:600}
.side-bottom{margin-top:auto;padding:14px;background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.04);border:1px solid #eee}
.side-user{display:flex;align-items:center;gap:10px}
.side-avatar{
  width:32px;height:32px;border-radius:50%;overflow:hidden;
  background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;color:#fff;
}
.side-avatar img{width:100%;height:100%;object-fit:cover}
.side-name{font-size:12.5px;color:#444;font-weight:500}
.side-role{font-size:10px;color:#aaa}

.content{flex:1;display:flex;flex-direction:column;overflow:hidden}
.topbar{
  padding:16px 24px;border-bottom:1px solid #eee;
  display:flex;align-items:center;justify-content:space-between;
  background:rgba(255,255,255,.5);
}
.topbar-left{display:flex;align-items:center;gap:14px}
.topbar-title{font-size:17px;font-weight:600;letter-spacing:-.3px;color:#1d1d1f}
.live-badge{
  display:flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;
  background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);font-size:10px;font-weight:600;color:#16a34a;
}
.live-dot{width:6px;height:6px;border-radius:50%;background:#16a34a;animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.8)}}
.topbar-right{display:flex;align-items:center;gap:8px}
.conn-badge{display:flex;align-items:center;gap:6px;padding:6px 14px;border-radius:20px;font-size:11px;font-weight:500}
.conn-sap{background:#eef4ff;color:#2563eb;border:1px solid #c7dbff}
.conn-sf{background:#edfcf2;color:#16a34a;border:1px solid #bbf7d0}
.conn-dot{width:5px;height:5px;border-radius:50%}
.conn-sap .conn-dot{background:#2563eb}
.conn-sf .conn-dot{background:#16a34a}

.report{padding:20px 24px;flex:1;overflow-y:auto}
.report-card{background:#fff;border:1px solid #eee;border-radius:16px;padding:22px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.03)}
.report-header{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.report-ai-icon{
  background:#1d1d1f;
  width:32px;height:32px;border-radius:10px;display:flex;align-items:center;
  justify-content:center;font-size:15px;color:#fff;
}
.report-title{font-size:16px;font-weight:600;color:#1d1d1f}
.report-subtitle{font-size:11px;color:#999;margin-top:1px}

.summary{font-size:13.5px;color:#555;line-height:1.75;margin-bottom:18px}
.summary .hl{background:#fef2f2;color:#dc2626;padding:2px 7px;border-radius:5px;font-weight:500}
.summary .hl-green{background:#f0fdf4;color:#16a34a;padding:2px 7px;border-radius:5px;font-weight:500}

.details-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
.detail-item{background:#fafafa;border:1px solid #eee;border-radius:12px;padding:14px}
.detail-label{font-size:10px;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.detail-val{font-size:15px;font-weight:600}
.detail-val.red{color:#dc2626}
.detail-val.green{color:#16a34a}
.detail-val.orange{color:#ea580c}
.detail-val.blue{color:#2563eb}
/* Sparkline in detail cards */
.sparkline{display:flex;align-items:end;gap:2px;height:24px;margin-top:8px}
.sparkline span{width:4px;border-radius:2px;display:block}
.sparkline .bar-red{background:rgba(220,38,38,.2)}
.sparkline .bar-green{background:rgba(22,163,74,.25)}
.sparkline .bar-orange{background:rgba(234,88,12,.2)}

.actions-title{font-size:13px;font-weight:600;margin-bottom:10px;color:#1d1d1f}
.action-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f5f5f5;font-size:13px}
.action-row:last-child{border:none}
.action-check{width:16px;height:16px;border:1.5px solid #ddd;border-radius:4px;flex-shrink:0}
.action-check.done{background:#16a34a;border-color:#16a34a}
.action-check.done::after{content:'✓';color:#fff;font-size:10px;display:flex;align-items:center;justify-content:center;font-weight:700;width:100%;height:100%}
.action-text{color:#666;flex:1}
.action-badge{font-size:10px;padding:4px 10px;border-radius:8px;font-weight:500;white-space:nowrap}
.ab-sap{background:#eef4ff;color:#2563eb;border:1px solid #c7dbff}
.ab-sf{background:#edfcf2;color:#16a34a;border:1px solid #bbf7d0}

.activity{margin-top:4px}
.activity-title{font-size:13px;font-weight:600;margin-bottom:12px;color:#1d1d1f}
.activity-item{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #f5f5f5}
.activity-item:last-child{border:none}
.activity-avatar{width:34px;height:34px;border-radius:50%;overflow:hidden;flex-shrink:0}
.activity-avatar img{width:100%;height:100%;object-fit:cover}
.activity-content{flex:1}
.activity-desc{font-size:13px;color:#555;line-height:1.5}
.activity-desc strong{color:#1d1d1f;font-weight:500}
.activity-meta{font-size:11px;color:#bbb;margin-top:3px;display:flex;align-items:center;gap:8px}
.activity-wave{display:flex;align-items:center;gap:1.5px;height:24px;margin-top:6px}
.activity-wave span{width:2.5px;border-radius:2px;display:block}
.wave-active{background:linear-gradient(to top,#ddd,#bbb)}

/* ============ FLOW CONNECTOR ============ */
.flow-connector{
  position:absolute;top:50%;right:300px;width:80px;height:2px;z-index:5;
  display:flex;align-items:center;justify-content:center;
}
.flow-line{
  width:100%;height:1px;
  background:linear-gradient(90deg,rgba(37,99,235,.3),rgba(168,85,247,.3),rgba(34,197,94,.3));
  position:relative;
}
.flow-particles{
  position:absolute;top:-3px;left:0;width:8px;height:8px;
  border-radius:50%;background:rgba(37,99,235,.4);
  animation:flowMove 3s ease-in-out infinite;
  box-shadow:0 0 8px rgba(37,99,235,.3);
}
@keyframes flowMove{0%{left:0;opacity:0}20%{opacity:1}80%{opacity:1}100%{left:calc(100% - 8px);opacity:0}}

/* ============ PHONE ============ */
.phone-wrap{
  width:340px;display:flex;align-items:center;justify-content:center;
  position:relative;z-index:2;margin-left:-30px;
}
/* Ambient glow */
.phone-wrap::before{
  content:'';position:absolute;width:260px;height:500px;
  background:radial-gradient(ellipse,rgba(37,99,235,.06) 0%,transparent 70%);
  border-radius:50%;filter:blur(30px);pointer-events:none;
}
.phone{
  width:290px;height:630px;background:#000;border-radius:44px;
  border:2.5px solid #444;overflow:hidden;display:flex;flex-direction:column;
  box-shadow:
    0 40px 100px rgba(0,0,0,.2),
    0 15px 40px rgba(0,0,0,.15),
    inset 0 1px 0 rgba(255,255,255,.08),
    0 0 0 1px rgba(0,0,0,.15);
  position:relative;
}
.phone-notch{width:100px;height:26px;background:#000;border-radius:0 0 14px 14px;margin:0 auto;position:relative}
.phone-notch::before{content:'';position:absolute;width:8px;height:8px;border-radius:50%;background:#1a1a1a;top:8px;left:50%;transform:translateX(-50%)}

.ph-header{padding:8px 16px 6px;border-bottom:1px solid #1a1a1a}
.ph-logo{display:flex;align-items:center;gap:6px;margin-bottom:6px}
.ph-logo img{height:14px;width:auto;filter:brightness(0) invert(1)}
.ph-badges{display:flex;gap:6px;justify-content:center;padding:4px 0}
.ph-badge{display:flex;align-items:center;gap:4px;padding:3px 8px;border-radius:10px;font-size:9px;font-weight:500}
.ph-badge-green{background:rgba(34,197,94,.1);color:#22c55e}
.ph-badge-grey{background:#111;color:#666}

.ph-messages{flex:1;padding:12px;overflow:hidden;display:flex;flex-direction:column;gap:8px}
.ph-msg{display:flex;gap:8px;align-items:flex-start}
.ph-msg-icon{width:26px;height:26px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center}
.ph-msg-icon.mic{background:#fff;color:#000}
.ph-msg-icon.ok{background:rgba(34,197,94,.15);color:#4ade80}
.ph-msg-bubble{background:#1a1a1a;border-radius:12px;padding:9px 11px;font-size:11px;line-height:1.55;color:#ccc;flex:1}
.ph-msg-bubble .hl{color:#f87171;font-weight:500}
.ph-msg-bubble .hl-g{color:#4ade80;font-weight:500}
.ph-msg-sys{background:#111;border:1px solid #1a1a1a;border-radius:10px;padding:6px 10px;font-size:10px;color:#666;flex:1}
.ph-msg-sys .ok{color:#4ade80}

.ph-ticket{
  border-radius:14px;
  background:linear-gradient(180deg,rgba(239,68,68,.12) 0%,rgba(239,68,68,.03) 100%);
  border:1px solid rgba(239,68,68,.2);padding:10px 12px;flex:1;
  backdrop-filter:blur(10px);
}
.ph-ticket-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.ph-ticket-name{font-size:12px;font-weight:600;color:#fff}
.ph-ticket-id{font-size:9px;color:#666;font-family:monospace}
.ph-ticket-badge{font-size:9px;padding:2px 7px;border-radius:6px;background:rgba(239,68,68,.15);color:#f87171;font-weight:600}
.ph-ticket-ref{font-size:10px;color:#666;margin-bottom:4px}
.ph-ticket-ref span{color:#fff;background:#1a1a1a;padding:1px 5px;border-radius:3px;font-family:monospace}
.ph-ticket-action-label{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px}
.ph-ticket-action{font-size:10px;color:#bbb;line-height:1.4}
.ph-ticket-footer{display:flex;align-items:center;justify-content:space-between;margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,.06)}
.ph-ticket-meta{font-size:9px;color:#444;display:flex;align-items:center;gap:4px}
.ph-ticket-meta .dot{width:4px;height:4px;border-radius:50%;background:#ef4444}
.ph-ticket-new{font-size:9px;padding:2px 6px;border-radius:4px;background:rgba(34,197,94,.15);color:#4ade80;font-weight:600}
.ph-export{margin:0 12px 4px;padding:7px;border-radius:10px;background:#fff;color:#000;font-size:10px;font-weight:600;text-align:center;display:flex;align-items:center;justify-content:center;gap:4px}

/* Phone footer with user photo */
.ph-footer{padding:10px 14px 18px;border-top:1px solid #1a1a1a;display:flex;flex-direction:column;gap:8px}
.ph-user-section{display:flex;align-items:center;gap:10px}
.ph-user-photo{
  width:40px;height:40px;border-radius:50%;overflow:hidden;flex-shrink:0;
  border:2px solid #22c55e;box-shadow:0 0 12px rgba(34,197,94,.3);
}
.ph-user-photo img{width:100%;height:100%;object-fit:cover}
.ph-user-info{flex:1}
.ph-user-name{font-size:12px;font-weight:600;color:#fff}
.ph-user-status{font-size:10px;color:#22c55e;display:flex;align-items:center;gap:4px}
.ph-user-status-dot{width:4px;height:4px;border-radius:50%;background:#22c55e;animation:pulse 2s ease-in-out infinite}
.ph-user-wave{display:flex;align-items:center;gap:1.5px;height:22px}
.ph-user-wave span{width:2px;border-radius:2px;display:block;background:#333}

/* Branding footer */
.powered{
  position:absolute;bottom:16px;left:50%;transform:translateX(-50%);
  font-size:10px;color:#bbb;display:flex;align-items:center;gap:6px;
  opacity:.6;z-index:10;
}
.powered img{height:12px;width:auto;opacity:.5}
</style>
</head>
<body>
<div class="scene">
  <div class="dashboard">
    <div class="side">
      <div class="side-logo"><img src="/showcase/logo" alt="Lexia"></div>
      <div class="side-section">Monitoring</div>
      <div class="side-item active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
        Service Requests
        <span class="badge">3</span>
      </div>
      <div class="side-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        Activity Log
      </div>
      <div class="side-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
        Alerts
      </div>
      <div class="side-section">Assets</div>
      <div class="side-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
        Equipment
      </div>
      <div class="side-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        Field Technicians
      </div>
      <div class="side-section">Analytics</div>
      <div class="side-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
        Reports
      </div>
      <div class="side-bottom">
        <div class="side-user">
          <div class="side-avatar"><img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face" alt=""></div>
          <div><div class="side-name">Hugo Martin</div><div class="side-role">Field Technician</div></div>
        </div>
      </div>
    </div>

    <div class="content">
      <div class="topbar">
        <div class="topbar-left">
          <div class="topbar-title">Valve V12 — Sector B3 · #SR-8920</div>
          <div class="live-badge"><div class="live-dot"></div>LIVE</div>
        </div>
        <div class="topbar-right">
          <div class="conn-badge conn-sap"><div class="conn-dot"></div>Synced to SAP</div>
          <div class="conn-badge conn-sf"><div class="conn-dot"></div>Synced to Salesforce</div>
        </div>
      </div>

      <div class="report">
        <div class="report-card">
          <div class="report-header">
            <div class="report-ai-icon">✦</div>
            <div><div class="report-title">AI Field Report</div><div class="report-subtitle">Auto-generated from voice input · 08:42 AM</div></div>
          </div>
          <div class="summary">
            <span class="hl">Leak detected</span> on <strong style="color:#1d1d1f">Valve V12</strong> in Sector B3, production line 2. The asset has logged <span class="hl-green">8,420 operating hours</span> since its last overhaul. A gasket kit replacement is recommended before resuming operations. Maintenance alert has been escalated to <span class="hl">maximum priority</span>.
          </div>

          <div style="font-size:13px;font-weight:600;margin-bottom:10px;color:#1d1d1f">Key Details</div>
          <div class="details-grid">
            <div class="detail-item">
              <div class="detail-label">Root Cause</div>
              <div class="detail-val red">Gasket Leak</div>
              <div class="sparkline">
                <span class="bar-red" style="height:8px"></span><span class="bar-red" style="height:12px"></span><span class="bar-red" style="height:10px"></span><span class="bar-red" style="height:16px"></span><span class="bar-red" style="height:22px"></span><span class="bar-red" style="height:24px"></span>
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-label">Operating Hours</div>
              <div class="detail-val orange">8,420 hrs</div>
              <div class="sparkline">
                <span class="bar-orange" style="height:4px"></span><span class="bar-orange" style="height:8px"></span><span class="bar-orange" style="height:10px"></span><span class="bar-orange" style="height:14px"></span><span class="bar-orange" style="height:18px"></span><span class="bar-orange" style="height:22px"></span>
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-label">Repair Status</div>
              <div class="detail-val green">In Progress</div>
              <div class="sparkline">
                <span class="bar-green" style="height:6px"></span><span class="bar-green" style="height:14px"></span><span class="bar-green" style="height:18px"></span><span class="bar-green" style="height:16px"></span><span class="bar-green" style="height:20px"></span><span class="bar-green" style="height:24px"></span>
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-label">Priority</div>
              <div class="detail-val red">Critical (5/5)</div>
              <div class="sparkline">
                <span class="bar-red" style="height:16px"></span><span class="bar-red" style="height:20px"></span><span class="bar-red" style="height:18px"></span><span class="bar-red" style="height:22px"></span><span class="bar-red" style="height:24px"></span><span class="bar-red" style="height:24px"></span>
              </div>
            </div>
          </div>

          <div class="actions-title">Next Actions Identified</div>
          <div class="action-row">
            <div class="action-check done"></div>
            <span class="action-text" style="color:#bbb;text-decoration:line-through">Order V12 gasket kit</span>
            <span class="action-badge ab-sap">Purchase order created in SAP</span>
          </div>
          <div class="action-row">
            <div class="action-check"></div>
            <span class="action-text">Schedule replacement within 48 hours</span>
            <span class="action-badge ab-sf">Opportunity created in Salesforce</span>
          </div>
          <div class="action-row">
            <div class="action-check"></div>
            <span class="action-text">Monitor pressure on circuit B3</span>
          </div>
        </div>

        <div class="activity">
          <div class="activity-title">Recent Activity</div>
          <div class="activity-item">
            <div class="activity-avatar"><img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face" alt=""></div>
            <div class="activity-content">
              <div class="activity-desc"><strong>Hugo Martin</strong> — Voice input from the field</div>
              <div class="activity-meta">08:42 AM · Voice Note · 12 sec</div>
              <div class="activity-desc" style="margin-top:6px;color:#888;font-style:italic">"There's a <span style="color:#dc2626">leak</span> on <strong style="color:#1d1d1f">valve V12</strong>, order a gasket kit and set the alert to max"</div>
              <div class="activity-wave">
                <span class="wave-active" style="height:3px"></span><span class="wave-active" style="height:9px"></span><span class="wave-active" style="height:15px"></span><span class="wave-active" style="height:11px"></span><span class="wave-active" style="height:20px"></span><span class="wave-active" style="height:14px"></span><span class="wave-active" style="height:7px"></span><span class="wave-active" style="height:18px"></span><span class="wave-active" style="height:22px"></span><span class="wave-active" style="height:16px"></span><span class="wave-active" style="height:9px"></span><span class="wave-active" style="height:20px"></span><span class="wave-active" style="height:12px"></span><span class="wave-active" style="height:5px"></span><span class="wave-active" style="height:14px"></span><span class="wave-active" style="height:18px"></span><span class="wave-active" style="height:10px"></span><span class="wave-active" style="height:16px"></span><span class="wave-active" style="height:7px"></span><span class="wave-active" style="height:12px"></span><span class="wave-active" style="height:20px"></span><span class="wave-active" style="height:14px"></span><span class="wave-active" style="height:5px"></span><span class="wave-active" style="height:10px"></span><span class="wave-active" style="height:16px"></span><span class="wave-active" style="height:8px"></span><span class="wave-active" style="height:4px"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Flow connector between dashboard and phone -->
  <div class="flow-connector">
    <div class="flow-line"><div class="flow-particles"></div></div>
  </div>

  <!-- ============ PHONE ============ -->
  <div class="phone-wrap">
    <div class="phone">
      <div class="phone-notch"></div>
      <div class="ph-header">
        <div class="ph-logo"><img src="/showcase/logo" alt="Lexia"></div>
        <div class="ph-badges">
          <div class="ph-badge ph-badge-green"><div style="width:4px;height:4px;border-radius:50%;background:#22c55e"></div> 100% Local</div>
          <div class="ph-badge ph-badge-grey"><svg style="width:10px;height:10px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg> Sovereign</div>
        </div>
      </div>

      <div class="ph-messages">
        <div class="ph-msg">
          <div class="ph-msg-icon ok"><svg style="width:12px;height:12px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 13l4 4L19 7"/></svg></div>
          <div class="ph-msg-sys"><span class="ok">Transcription complete</span></div>
        </div>
        <div class="ph-msg">
          <div class="ph-msg-icon mic"><svg style="width:11px;height:11px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg></div>
          <div class="ph-msg-bubble">There's a <span class="hl">leak</span> on <span class="hl-g">valve V12</span>, order a gasket kit and set the alert to max</div>
        </div>
        <div class="ph-msg">
          <div class="ph-msg-icon ok"><svg style="width:12px;height:12px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 13l4 4L19 7"/></svg></div>
          <div class="ph-msg-sys"><span class="ok">Ticket created successfully</span></div>
        </div>
        <div class="ph-msg" style="padding-left:34px">
          <div class="ph-ticket">
            <div class="ph-ticket-head">
              <div><div class="ph-ticket-name">Valve V12</div><div class="ph-ticket-id">TKT-084215</div></div>
              <div class="ph-ticket-badge">Critical</div>
            </div>
            <div class="ph-ticket-ref">Ref: <span>V12 Gasket Kit</span></div>
            <div class="ph-ticket-action-label">REQUIRED ACTION</div>
            <div class="ph-ticket-action">Order gasket kit and escalate alert to maximum</div>
            <div class="ph-ticket-footer">
              <div class="ph-ticket-meta"><div class="dot"></div> Priority 5/5 · 08:42</div>
              <div class="ph-ticket-new">New</div>
            </div>
          </div>
        </div>
        <div style="text-align:center;padding:4px 0">
          <span style="display:inline-flex;align-items:center;gap:4px;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.15);color:#4ade80;font-size:9px;padding:3px 10px;border-radius:12px;font-weight:500">
            <svg style="width:10px;height:10px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 13l4 4L19 7"/></svg>
            Ticket saved — TKT-084215
          </span>
        </div>
      </div>

      <div class="ph-export">
        <svg style="width:12px;height:12px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4L12 14M12 14L8 10M12 14L16 10"/><path d="M4 17v1a2 2 0 002 2h12a2 2 0 002-2v-1"/></svg>
        Export to SAP
      </div>

      <div class="ph-footer">
        <div class="ph-user-section">
          <div class="ph-user-photo"><img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face" alt="Hugo Martin"></div>
          <div class="ph-user-info">
            <div class="ph-user-name">Hugo Martin</div>
            <div class="ph-user-status"><div class="ph-user-status-dot"></div>Recording complete</div>
          </div>
          <div class="ph-user-wave">
            <span style="height:4px"></span><span style="height:10px"></span><span style="height:16px"></span><span style="height:12px"></span><span style="height:20px"></span><span style="height:14px"></span><span style="height:8px"></span><span style="height:18px"></span><span style="height:22px"></span><span style="height:14px"></span><span style="height:8px"></span><span style="height:4px"></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="powered">
  <span>Powered by</span>
  <img src="/showcase/logo" alt="Lexia">
</div>
</body>
</html>"""


@app.get("/showcase-long", response_class=HTMLResponse)
async def showcase_long_context():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Lexia — Secure Intelligence for the Boardroom</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  background:#e8e9ec;color:#1d1d1f;height:100vh;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
  -webkit-font-smoothing:antialiased;
}
.win{
  width:1200px;height:700px;background:#fff;border-radius:12px;overflow:hidden;
  border:1px solid #d4d4d8;box-shadow:0 24px 80px rgba(0,0,0,.1);
  display:flex;flex-direction:column;
}
.tb{
  height:40px;background:#f8f8f8;border-bottom:1px solid #e4e4e7;
  display:flex;align-items:center;padding:0 16px;flex-shrink:0;
}
.dots{display:flex;gap:8px}
.dots span{width:12px;height:12px;border-radius:50%}
.d1{background:#ff5f57}.d2{background:#febc2e}.d3{background:#28c840}
.tb-c{flex:1;display:flex;align-items:center;justify-content:center;margin-right:56px;gap:8px}
.tb-c img{height:15px}
.tb-c span{font-size:12px;color:#a1a1aa;font-weight:500}
.tb-sep{width:1px;height:12px;background:#d4d4d8}

.main{flex:1;display:flex;overflow:hidden}

/* LEFT */
.left{width:360px;background:#fafafa;border-right:1px solid #e4e4e7;display:flex;flex-direction:column}
.lh{padding:24px 24px 20px}
.lh h2{font-size:16px;font-weight:600;color:#18181b;letter-spacing:-.2px}
.lh p{font-size:12px;color:#a1a1aa;margin-top:3px}
.sec{margin:0 24px;padding:10px 0;display:flex;align-items:center;gap:6px;font-size:11px;color:#15803d;font-weight:500}
.sec svg{width:13px;height:13px}
.rec{margin:0 24px;padding:20px 0;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #f0f0f0}
.rec-l{display:flex;align-items:center;gap:7px}
.rec-d{width:7px;height:7px;border-radius:50%;background:#ef4444;animation:p 1.5s ease-in-out infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.3}}
.rec-t{font-size:12px;font-weight:500;color:#ef4444}
.timer{font-size:22px;font-weight:600;color:#18181b;font-family:'SF Mono',monospace;letter-spacing:.5px}
.ppl{padding:16px 24px;flex:1;border-top:1px solid #f0f0f0}
.ppl-t{font-size:10px;color:#a1a1aa;text-transform:uppercase;letter-spacing:.8px;font-weight:600;margin-bottom:12px}
.pp{display:flex;align-items:center;gap:10px;padding:7px 0}
.pp-av{width:32px;height:32px;border-radius:50%;overflow:hidden;flex-shrink:0;position:relative}
.pp-av img{width:100%;height:100%;object-fit:cover}
.pp-ring{position:absolute;inset:-2px;border-radius:50%;border:2px solid #2563eb}
.pp-n{font-size:13px;font-weight:500;color:#18181b}
.pp-r{font-size:11px;color:#a1a1aa}
.pp-i{flex:1}
.pp-s{font-size:9px;font-weight:500;color:#2563eb;background:#eff6ff;padding:2px 6px;border-radius:3px}

/* RIGHT */
.right{flex:1;display:flex;flex-direction:column;overflow:hidden}
.rh{padding:16px 28px;border-bottom:1px solid #e4e4e7;display:flex;align-items:center;justify-content:space-between}
.rh-l{display:flex;align-items:center;gap:8px}
.rh-l span{font-size:15px;font-weight:600;color:#18181b}
.rh-tag{font-size:10px;color:#a1a1aa;font-weight:500}
.rc{flex:1;overflow-y:auto;padding:24px 28px}

.st{font-size:11px;font-weight:600;color:#a1a1aa;text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px}
.txt{font-size:13.5px;color:#52525b;line-height:1.75;margin-bottom:28px}
.txt strong{color:#18181b}
.hr{background:#fef2f2;color:#dc2626;padding:1px 5px;border-radius:3px;font-weight:500;font-size:12.5px}
.hg{background:#f0fdf4;color:#15803d;padding:1px 5px;border-radius:3px;font-weight:500;font-size:12.5px}
.hb{background:#eff6ff;color:#1d4ed8;padding:1px 5px;border-radius:3px;font-weight:500;font-size:12.5px}

.dl{display:flex;flex-direction:column;gap:4px;margin-bottom:28px}
.di{display:flex;align-items:baseline;gap:8px;padding:8px 0;border-bottom:1px solid #f5f5f5}
.di:last-child{border:none}
.dn{font-size:11px;font-weight:600;color:#2563eb;flex-shrink:0;width:16px}
.dt{font-size:13px;color:#3f3f46;line-height:1.5}
.dt strong{color:#18181b}
.dm{font-size:10px;color:#a1a1aa;margin-top:2px}

.al{display:flex;flex-direction:column;gap:4px}
.ai{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f5f5f5}
.ai:last-child{border:none}
.ab{width:3px;height:20px;border-radius:1.5px;flex-shrink:0}
.ab-r{background:#ef4444}.ab-a{background:#f59e0b}
.at{font-size:13px;color:#18181b;font-weight:500;flex:1}
.as{font-size:11px;color:#a1a1aa}
.ad{font-size:10px;color:#71717a;font-weight:500;white-space:nowrap}
</style>
</head>
<body>
<div class="win">
  <div class="tb">
    <div class="dots"><span class="d1"></span><span class="d2"></span><span class="d3"></span></div>
    <div class="tb-c">
      <img src="/showcase/logo" alt="Lexia">
      <div class="tb-sep"></div>
      <span>Meeting Intelligence</span>
    </div>
  </div>
  <div class="main">
    <div class="left">
      <div class="lh">
        <h2>Q1 Strategic Planning</h2>
        <p>Board Room A · Feb 11, 2026</p>
      </div>
      <div class="sec">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
        Local processing only
      </div>
      <div class="rec">
        <div class="rec-l"><div class="rec-d"></div><div class="rec-t">Recording</div></div>
        <div class="timer">01:24:36</div>
      </div>
      <div class="ppl">
        <div class="ppl-t">Participants</div>
        <div class="pp">
          <div class="pp-av"><img src="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=100&h=100&fit=crop&crop=face" alt=""><div class="pp-ring"></div></div>
          <div class="pp-i"><div class="pp-n">Marc Dubois</div><div class="pp-r">CEO</div></div>
          <div class="pp-s">Speaking</div>
        </div>
        <div class="pp">
          <div class="pp-av"><img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=100&h=100&fit=crop&crop=face" alt=""></div>
          <div class="pp-i"><div class="pp-n">Claire Fontaine</div><div class="pp-r">CFO</div></div>
        </div>
        <div class="pp">
          <div class="pp-av"><img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face" alt=""></div>
          <div class="pp-i"><div class="pp-n">Hugo Martin</div><div class="pp-r">VP Operations</div></div>
        </div>
        <div class="pp">
          <div class="pp-av"><img src="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100&h=100&fit=crop&crop=face" alt=""></div>
          <div class="pp-i"><div class="pp-n">Sophie Laurent</div><div class="pp-r">CTO</div></div>
        </div>
      </div>
    </div>
    <div class="right">
      <div class="rh">
        <div class="rh-l"><span>Executive Summary</span></div>
        <div class="rh-tag">AI-generated</div>
      </div>
      <div class="rc">
        <div class="st">Summary</div>
        <div class="txt">
          The board reviewed <strong>Q1 performance</strong> against strategic objectives. Revenue grew <span class="hg">+18% YoY</span> driven by the enterprise segment. <strong>Operating margins</strong> under pressure at <span class="hr">-2.3 pts</span> due to accelerated hiring. <strong>APAC expansion</strong> confirmed for <span class="hb">Singapore</span> and <span class="hb">Tokyo</span> in Q2. A <span class="hr">supply chain risk</span> flagged on critical components.
        </div>

        <div class="st">Decisions</div>
        <div class="dl">
          <div class="di">
            <div class="dn">1</div>
            <div><div class="dt"><strong>Approve APAC expansion budget</strong> — 2.4M for Singapore and Tokyo in Q2.</div><div class="dm">Marc Dubois · Effective immediately</div></div>
          </div>
          <div class="di">
            <div class="dn">2</div>
            <div><div class="dt"><strong>Freeze non-critical hiring</strong> until margins recover above 22%.</div><div class="dm">Claire Fontaine · March 1</div></div>
          </div>
          <div class="di">
            <div class="dn">3</div>
            <div><div class="dt"><strong>Dual-source critical components</strong> to mitigate supply chain risk.</div><div class="dm">Hugo Martin · Feb 28</div></div>
          </div>
        </div>

        <div class="st">Action Items</div>
        <div class="al">
          <div class="ai">
            <div class="ab ab-r"></div>
            <div class="at">Draft supply chain mitigation plan</div>
            <div class="as">Hugo Martin</div>
            <div class="ad">Feb 28</div>
          </div>
          <div class="ai">
            <div class="ab ab-r"></div>
            <div class="at">Finalize Singapore office lease</div>
            <div class="as">Marc Dubois</div>
            <div class="ad">Mar 5</div>
          </div>
          <div class="ai">
            <div class="ab ab-a"></div>
            <div class="at">Revise hiring budget</div>
            <div class="as">Claire Fontaine</div>
            <div class="ad">Mar 10</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
