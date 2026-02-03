#!/usr/bin/env python3
"""
Lexia Stream - Modern Voice Transcription App
"""

import sys
import os
import tempfile
import threading
import time
import math
import wave
import json
from pathlib import Path

import numpy as np
import sounddevice as sd
import requests
from scipy.io import wavfile

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QPainter, QPainterPath

import webbrowser
import http.server
import socketserver

try:
    import pyperclip
    PASTE_AVAILABLE = True
except:
    PASTE_AVAILABLE = False

try:
    from pynput import keyboard
    from pynput.keyboard import Key, Controller as KeyboardController
    HOTKEY_AVAILABLE = True
    kb_controller = KeyboardController()
except:
    HOTKEY_AVAILABLE = False
    kb_controller = None
    print("⚠️ pynput not available - hotkey disabled")

BACKEND_URL = "http://localhost:8000"
SAMPLE_RATE = 16000


class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.stream = None
        self.level = 0.0
    
    def start(self):
        self.audio_data = []
        self.recording = True
        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', callback=self._cb)
        self.stream.start()
    
    def _cb(self, data, frames, t, status):
        if self.recording:
            self.audio_data.append(data.copy())
            self.level = min(1.0, np.abs(data).mean() / 3000.0)
    
    def stop(self):
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if not self.audio_data:
            return None
        audio = np.concatenate(self.audio_data, axis=0)
        f = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        wavfile.write(f.name, SAMPLE_RATE, audio)
        return f.name


class Signals(QObject):
    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    open_settings = pyqtSignal()


# ============== STOCKAGE LOCAL ==============
class LocalStorage:
    """Gère la persistance des données en local."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".lexia-stream"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.data = self._load()
    
    def _load(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"word_boost": [], "history": []}
    
    def save(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_word_boost(self) -> list:
        return self.data.get("word_boost", [])
    
    def add_word(self, word: str):
        word = word.strip()
        if word and word not in self.data["word_boost"]:
            self.data["word_boost"].append(word)
            self.save()
    
    def remove_word(self, word: str):
        if word in self.data["word_boost"]:
            self.data["word_boost"].remove(word)
            self.save()
    
    def add_to_history(self, text: str):
        self.data.setdefault("history", [])
        self.data["history"].insert(0, {"text": text, "time": time.strftime("%Y-%m-%d %H:%M")})
        self.data["history"] = self.data["history"][:50]  # Garder 50 derniers
        self.save()


# Instance globale
storage = LocalStorage()


# ============== FENÊTRE LEXIA STREAM (WEBVIEW) ==============

class LexiaStreamAPI:
    """API pour la communication JavaScript -> Python."""
    
    def __init__(self):
        self._window = None
    
    def set_window(self, window):
        self._window = window
    
    def add_word(self, word):
        """Ajoute un mot au word boost."""
        if word and word.strip():
            storage.add_word(word.strip())
            self._refresh_window()
        return True
    
    def remove_word(self, word):
        """Supprime un mot du word boost."""
        storage.remove_word(word)
        self._refresh_window()
        return True
    
    def get_data(self):
        """Récupère les données pour l'interface."""
        history = storage.data.get("history", [])
        words = storage.get_word_boost()
        total_words = sum(len(h.get("text", "").split()) for h in history)
        return {
            "history": history[:20],
            "words": words,
            "stats": {
                "transcriptions": len(history),
                "words": total_words,
                "boost": len(words)
            }
        }
    
    def _refresh_window(self):
        if self._window:
            self._window.evaluate_js('refreshData()')


def get_html():
    """Génère le HTML de l'interface."""
    return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lexia Stream</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', system-ui, sans-serif;
            background: #09090b;
            color: #fafafa;
            height: 100vh;
            overflow: hidden;
        }
        
        .container { display: flex; height: 100vh; }
        
        .sidebar {
            width: 200px;
            background: #09090b;
            border-right: 1px solid #27272a;
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 32px;
        }
        
        .logo-icon {
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, #a855f7, #ec4899, #f97316);
            border-radius: 8px;
        }
        
        .logo-text {
            font-size: 16px;
            font-weight: 700;
        }
        
        .nav { display: flex; flex-direction: column; gap: 4px; flex: 1; }
        
        .nav-item {
            padding: 12px 14px;
            border-radius: 10px;
            cursor: pointer;
            color: #71717a;
            font-size: 14px;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .nav-item:hover { background: #18181b; color: #fafafa; }
        .nav-item.active { background: #27272a; color: #fafafa; font-weight: 500; }
        
        .nav-item svg { width: 20px; height: 20px; opacity: 0.7; }
        
        .shortcut {
            padding: 14px;
            background: #18181b;
            border-radius: 10px;
            font-size: 12px;
            color: #52525b;
            line-height: 1.6;
        }
        
        .shortcut kbd {
            background: #27272a;
            padding: 3px 8px;
            border-radius: 6px;
            font-family: inherit;
            color: #a1a1aa;
            font-size: 11px;
        }
        
        .content { flex: 1; padding: 28px 32px; overflow-y: auto; }
        
        .page { display: none; }
        .page.active { display: block; animation: fadeIn 0.2s ease; }
        
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        
        .stats { display: flex; gap: 16px; margin-bottom: 32px; }
        
        .stat-card {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 14px;
            padding: 20px 24px;
            min-width: 130px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f97316 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            font-size: 12px;
            color: #52525b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 6px;
        }
        
        .section-title {
            font-size: 13px;
            font-weight: 600;
            color: #52525b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
        }
        
        .history-list {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 14px;
            overflow: hidden;
        }
        
        .history-item {
            padding: 16px 20px;
            border-bottom: 1px solid #27272a;
            display: flex;
            gap: 20px;
            transition: background 0.15s ease;
        }
        
        .history-item:last-child { border-bottom: none; }
        .history-item:hover { background: #1f1f23; }
        
        .history-item .time { color: #52525b; font-size: 13px; min-width: 55px; }
        .history-item .text { color: #a1a1aa; font-size: 14px; line-height: 1.4; }
        
        .input-row { display: flex; gap: 12px; margin-bottom: 24px; }
        
        .input-row input {
            flex: 1;
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 10px;
            padding: 14px 18px;
            color: #fafafa;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s ease;
        }
        
        .input-row input:focus { border-color: #a855f7; }
        .input-row input::placeholder { color: #52525b; }
        
        .btn-primary {
            background: linear-gradient(135deg, #7c3aed 0%, #db2777 50%, #ea580c 100%);
            border: none;
            border-radius: 10px;
            padding: 14px 24px;
            color: white;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s ease, transform 0.1s ease;
        }
        
        .btn-primary:hover { opacity: 0.9; }
        .btn-primary:active { transform: scale(0.98); }
        
        .words-grid { display: flex; flex-wrap: wrap; gap: 10px; }
        
        .word-chip {
            background: #27272a;
            border-radius: 10px;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            transition: background 0.15s ease;
        }
        
        .word-chip:hover { background: #3f3f46; }
        
        .word-chip .remove-btn {
            background: none;
            border: none;
            color: #52525b;
            cursor: pointer;
            font-size: 18px;
            padding: 0;
            line-height: 1;
            transition: color 0.15s ease;
        }
        
        .word-chip .remove-btn:hover { color: #ef4444; }
        
        .empty-state {
            color: #52525b;
            font-size: 14px;
            text-align: center;
            padding: 48px;
        }
        
        .page-title { font-size: 26px; font-weight: 600; margin-bottom: 8px; }
        .page-subtitle { color: #71717a; font-size: 15px; margin-bottom: 28px; }
        
        .history-full-item {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 14px;
            transition: border-color 0.15s ease;
        }
        
        .history-full-item:hover { border-color: #3f3f46; }
        
        .history-time { font-size: 12px; color: #52525b; margin-bottom: 10px; }
        .history-text { font-size: 14px; color: #a1a1aa; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="logo">
                <div class="logo-icon"></div>
                <span class="logo-text">Lexia Stream</span>
            </div>
            
            <div class="nav">
                <div class="nav-item active" onclick="showPage('home')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                    Home
                </div>
                <div class="nav-item" onclick="showPage('dictionary')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
                    Dictionary
                </div>
                <div class="nav-item" onclick="showPage('history')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    History
                </div>
            </div>
            
            <div class="shortcut">
                <kbd>↓</kbd> enregistrer<br>
                <kbd>⌘↓</kbd> ouvrir
            </div>
        </div>
        
        <div class="content">
            <div id="page-home" class="page active">
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value" id="stat-trans">0</div>
                        <div class="stat-label">Transcriptions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-words">0</div>
                        <div class="stat-label">Mots</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-boost">0</div>
                        <div class="stat-label">Word Boost</div>
                    </div>
                </div>
                
                <div class="section-title">Récent</div>
                <div class="history-list" id="recent-list"></div>
            </div>
            
            <div id="page-dictionary" class="page">
                <div class="page-title">Dictionary</div>
                <div class="page-subtitle">Ajoutez des mots pour améliorer leur reconnaissance</div>
                
                <div class="input-row">
                    <input type="text" id="word-input" placeholder="Ajouter un mot..." onkeypress="if(event.key==='Enter')addWord()">
                    <button class="btn-primary" onclick="addWord()">Ajouter</button>
                </div>
                
                <div class="words-grid" id="words-grid"></div>
            </div>
            
            <div id="page-history" class="page">
                <div class="page-title">History</div>
                <div class="page-subtitle">Toutes vos transcriptions</div>
                <div id="full-history"></div>
            </div>
        </div>
    </div>
    
    <script>
        function showPage(pageId) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('page-' + pageId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
        
        async function refreshData() {
            try {
                const data = await pywebview.api.get_data();
                
                document.getElementById('stat-trans').textContent = data.stats.transcriptions;
                document.getElementById('stat-words').textContent = data.stats.words;
                document.getElementById('stat-boost').textContent = data.stats.boost;
                
                const recentList = document.getElementById('recent-list');
                if (data.history.length === 0) {
                    recentList.innerHTML = '<div class="empty-state">Appuyez sur ↓ pour dicter</div>';
                } else {
                    recentList.innerHTML = data.history.slice(0, 10).map(item => {
                        const time = item.time ? item.time.split(' ').pop() : '';
                        const text = item.text.length > 80 ? item.text.substring(0, 80) + '...' : item.text;
                        return `<div class="history-item"><span class="time">${time}</span><span class="text">${text}</span></div>`;
                    }).join('');
                }
                
                const wordsGrid = document.getElementById('words-grid');
                if (data.words.length === 0) {
                    wordsGrid.innerHTML = '<div class="empty-state">Aucun mot ajouté</div>';
                } else {
                    wordsGrid.innerHTML = data.words.map(word => 
                        `<div class="word-chip"><span>${word}</span><button class="remove-btn" onclick="removeWord('${word}')">×</button></div>`
                    ).join('');
                }
                
                const fullHistory = document.getElementById('full-history');
                if (data.history.length === 0) {
                    fullHistory.innerHTML = '<div class="empty-state">Aucune transcription</div>';
                } else {
                    fullHistory.innerHTML = data.history.map(item => 
                        `<div class="history-full-item"><div class="history-time">${item.time}</div><div class="history-text">${item.text}</div></div>`
                    ).join('');
                }
            } catch(e) {
                console.error('Error refreshing:', e);
            }
        }
        
        async function addWord() {
            const input = document.getElementById('word-input');
            const word = input.value.trim();
            if (word) {
                await pywebview.api.add_word(word);
                input.value = '';
                refreshData();
            }
        }
        
        async function removeWord(word) {
            await pywebview.api.remove_word(word);
            refreshData();
        }
        
        window.addEventListener('pywebviewready', refreshData);
    </script>
</body>
</html>'''


class LexiaStreamServer:
    """Serveur HTTP simple pour l'interface."""
    
    _server = None
    _port = 9999
    _running = False
    _base_dir = os.path.dirname(__file__)
    
    @classmethod
    def start(cls):
        if cls._running:
            return
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self_handler):
                if self_handler.path == '/' or self_handler.path == '/index.html':
                    self_handler.send_response(200)
                    self_handler.send_header('Content-type', 'text/html')
                    self_handler.end_headers()
                    html = get_html_with_data()
                    self_handler.wfile.write(html.encode())
                elif self_handler.path == '/logo.png':
                    logo_path = os.path.join(cls._base_dir, 'logo.png')
                    if os.path.exists(logo_path):
                        self_handler.send_response(200)
                        self_handler.send_header('Content-type', 'image/png')
                        self_handler.end_headers()
                        with open(logo_path, 'rb') as f:
                            self_handler.wfile.write(f.read())
                    else:
                        self_handler.send_response(404)
                        self_handler.end_headers()
                elif self_handler.path == '/api/data':
                    self_handler.send_response(200)
                    self_handler.send_header('Content-type', 'application/json')
                    self_handler.send_header('Access-Control-Allow-Origin', '*')
                    self_handler.end_headers()
                    data = {
                        "history": storage.data.get("history", [])[:50],
                        "words": storage.get_word_boost(),
                        "stats": {
                            "transcriptions": len(storage.data.get("history", [])),
                            "words": sum(len(h.get("text", "").split()) for h in storage.data.get("history", [])),
                            "boost": len(storage.get_word_boost())
                        }
                    }
                    self_handler.wfile.write(json.dumps(data).encode())
                elif self_handler.path.startswith('/api/add/'):
                    word = self_handler.path.split('/api/add/')[-1]
                    if word:
                        import urllib.parse
                        storage.add_word(urllib.parse.unquote(word))
                    self_handler.send_response(200)
                    self_handler.send_header('Content-type', 'text/plain')
                    self_handler.end_headers()
                    self_handler.wfile.write(b'ok')
                elif self_handler.path.startswith('/api/remove/'):
                    word = self_handler.path.split('/api/remove/')[-1]
                    if word:
                        import urllib.parse
                        storage.remove_word(urllib.parse.unquote(word))
                    self_handler.send_response(200)
                    self_handler.send_header('Content-type', 'text/plain')
                    self_handler.end_headers()
                    self_handler.wfile.write(b'ok')
                else:
                    self_handler.send_response(404)
                    self_handler.end_headers()
            
            def log_message(self_handler, format, *args):
                pass
        
        def run_server():
            with socketserver.TCPServer(("", cls._port), Handler) as httpd:
                cls._server = httpd
                cls._running = True
                httpd.serve_forever()
        
        threading.Thread(target=run_server, daemon=True).start()
        time.sleep(0.3)


def get_html_with_data():
    """Génère le HTML avec les données intégrées."""
    history = storage.data.get("history", [])
    words = storage.get_word_boost()
    total_words = sum(len(h.get("text", "").split()) for h in history)
    
    # Build HTML parts separately
    recent_html = ""
    for i, item in enumerate(history[:8]):
        t = item.get("time", "").split(" ")[-1] if item.get("time") else ""
        txt = item.get("text", "")[:100]
        full_txt = item.get("text", "").replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
        if len(item.get("text", "")) > 100:
            txt += "..."
        recent_html += f'''<div class="history-item" onclick="copyText('{full_txt}')">
            <div class="item-content"><span class="time">{t}</span><span class="text">{txt}</span></div>
            <button class="copy-btn" title="Copier"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button>
        </div>'''
    if not recent_html:
        recent_html = '<div class="empty-state"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><path d="M12 18.5a6.5 6.5 0 100-13 6.5 6.5 0 000 13z"/><path d="M12 15v-3m0-3h.01"/></svg><p>Appuyez sur ↓ pour dicter</p></div>'
    
    words_html = ""
    for word in words:
        safe_word = word.replace("'", "\\'")
        words_html += f'''<div class="word-chip"><span class="word-text">{word}</span><button class="remove-btn" onclick="event.stopPropagation(); removeWord('{safe_word}')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>'''
    if not words_html:
        words_html = '<div class="empty-state small"><p>Ajoutez des mots pour améliorer la reconnaissance</p></div>'
    
    history_html = ""
    for item in history:
        txt = item.get("text", "")
        safe_txt = txt.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
        history_html += f'''<div class="history-full-item">
            <div class="history-header"><span class="history-time">{item.get("time", "")}</span><button class="copy-btn-sm" onclick="copyText('{safe_txt}')" title="Copier"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button></div>
            <div class="history-text">{txt}</div>
        </div>'''
    if not history_html:
        history_html = '<div class="empty-state"><p>Aucune transcription</p></div>'
    
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lexia Stream</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', system-ui, sans-serif;
            background: #0a0a0a;
            color: #fafafa;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{ display: flex; min-height: 100vh; }}
        
        /* Sidebar */
        .sidebar {{
            width: 240px;
            background: linear-gradient(180deg, #0f0f0f 0%, #0a0a0a 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
        }}
        .logo {{ display: flex; align-items: center; gap: 14px; margin-bottom: 40px; padding: 0 8px; }}
        .logo img {{ height: 70px; width: auto; }}
        .logo-text {{ font-size: 18px; font-weight: 600; letter-spacing: -0.3px; }}
        
        .nav {{ display: flex; flex-direction: column; gap: 4px; flex: 1; }}
        .nav-item {{
            padding: 12px 16px;
            border-radius: 10px;
            cursor: pointer;
            color: #6b6b6b;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }}
        .nav-item:hover {{ background: rgba(255,255,255,0.04); color: #a1a1a1; }}
        .nav-item.active {{ background: rgba(255,255,255,0.08); color: #fafafa; }}
        .nav-item svg {{ width: 20px; height: 20px; opacity: 0.7; }}
        
        .shortcut {{
            padding: 14px 16px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            font-size: 12px;
            color: #4a4a4a;
            line-height: 2;
        }}
        .shortcut kbd {{
            background: rgba(255,255,255,0.08);
            padding: 3px 8px;
            border-radius: 6px;
            font-family: 'SF Mono', monospace;
            color: #888;
            font-size: 11px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        /* Content */
        .content {{ flex: 1; padding: 32px 48px; margin-left: 240px; max-width: 900px; }}
        .page {{ display: none; animation: fadeIn 0.2s ease; }}
        .page.active {{ display: block; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        
        /* Stats */
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 48px; }}
        .stat-card {{
            background: linear-gradient(135deg, rgba(168,85,247,0.08) 0%, rgba(236,72,153,0.05) 50%, rgba(249,115,22,0.03) 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.2s ease;
        }}
        .stat-card:hover {{ border-color: rgba(255,255,255,0.15); transform: translateY(-2px); }}
        .stat-value {{
            font-size: 40px;
            font-weight: 700;
            background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f97316 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
        }}
        .stat-label {{ font-size: 12px; color: #525252; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px; font-weight: 500; }}
        
        /* Section */
        .section-title {{ font-size: 12px; font-weight: 600; color: #525252; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }}
        
        /* History List */
        .history-list {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; overflow: hidden; }}
        .history-item {{
            padding: 16px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .history-item:last-child {{ border-bottom: none; }}
        .history-item:hover {{ background: rgba(255,255,255,0.03); }}
        .history-item:active {{ background: rgba(168,85,247,0.1); }}
        .item-content {{ display: flex; align-items: center; gap: 16px; flex: 1; min-width: 0; }}
        .history-item .time {{ color: #4a4a4a; font-size: 13px; font-family: 'SF Mono', monospace; min-width: 50px; }}
        .history-item .text {{ color: #a1a1a1; font-size: 14px; line-height: 1.5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .copy-btn {{
            background: none;
            border: none;
            color: #4a4a4a;
            cursor: pointer;
            padding: 8px;
            border-radius: 8px;
            transition: all 0.15s ease;
            opacity: 0;
        }}
        .history-item:hover .copy-btn {{ opacity: 1; }}
        .copy-btn:hover {{ background: rgba(255,255,255,0.1); color: #a855f7; }}
        
        /* Input */
        .input-row {{ display: flex; gap: 12px; margin-bottom: 32px; }}
        .input-row input {{
            flex: 1;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 14px 18px;
            color: #fafafa;
            font-size: 14px;
            outline: none;
            transition: all 0.2s ease;
        }}
        .input-row input:focus {{ border-color: #a855f7; background: rgba(168,85,247,0.05); }}
        .input-row input::placeholder {{ color: #4a4a4a; }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            color: white;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(168,85,247,0.3);
        }}
        .btn-primary:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(168,85,247,0.4); }}
        .btn-primary:active {{ transform: translateY(0); }}
        
        /* Word chips */
        .words-grid {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .word-chip {{
            background: rgba(168,85,247,0.1);
            border: 1px solid rgba(168,85,247,0.2);
            border-radius: 10px;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: #c4b5fd;
            transition: all 0.15s ease;
        }}
        .word-chip:hover {{ background: rgba(168,85,247,0.15); border-color: rgba(168,85,247,0.3); }}
        .word-chip .remove-btn {{
            background: none;
            border: none;
            color: #6b6b6b;
            cursor: pointer;
            padding: 2px;
            display: flex;
            transition: color 0.15s ease;
        }}
        .word-chip .remove-btn:hover {{ color: #ef4444; }}
        
        /* Empty state */
        .empty-state {{ color: #4a4a4a; font-size: 14px; text-align: center; padding: 60px 20px; display: flex; flex-direction: column; align-items: center; gap: 16px; }}
        .empty-state.small {{ padding: 40px 20px; }}
        .empty-state p {{ max-width: 240px; line-height: 1.5; }}
        
        /* Page titles */
        .page-title {{ font-size: 28px; font-weight: 600; margin-bottom: 8px; letter-spacing: -0.5px; }}
        .page-subtitle {{ color: #6b6b6b; font-size: 15px; margin-bottom: 32px; }}
        
        /* Full history */
        .history-full-item {{
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 12px;
            transition: all 0.15s ease;
        }}
        .history-full-item:hover {{ border-color: rgba(255,255,255,0.12); }}
        .history-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .history-time {{ font-size: 12px; color: #4a4a4a; font-family: 'SF Mono', monospace; }}
        .history-text {{ font-size: 14px; color: #a1a1a1; line-height: 1.7; }}
        .copy-btn-sm {{
            background: none;
            border: none;
            color: #4a4a4a;
            cursor: pointer;
            padding: 6px;
            border-radius: 6px;
            transition: all 0.15s ease;
            display: flex;
        }}
        .copy-btn-sm:hover {{ background: rgba(255,255,255,0.1); color: #a855f7; }}
        
        /* Toast */
        .toast {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: #1a1a1a;
            border: 1px solid rgba(255,255,255,0.1);
            padding: 12px 20px;
            border-radius: 10px;
            font-size: 13px;
            color: #a1a1a1;
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        .toast.show {{ transform: translateX(-50%) translateY(0); opacity: 1; }}
        .toast.success {{ border-color: rgba(34,197,94,0.3); color: #22c55e; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="logo">
                <img src="/logo.png" alt="Lexia Stream">
            </div>
            <div class="nav">
                <a class="nav-item active" onclick="showPage('home', this)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                    Home
                </a>
                <a class="nav-item" onclick="showPage('dictionary', this)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
                    Dictionary
                </a>
                <a class="nav-item" onclick="showPage('history', this)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    History
                </a>
            </div>
            <div class="shortcut">
                <kbd>↓</kbd> enregistrer<br>
                <kbd>⌘↓</kbd> ouvrir
            </div>
        </div>
        <div class="content">
            <div id="page-home" class="page active">
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">{len(history)}</div>
                        <div class="stat-label">Transcriptions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{total_words}</div>
                        <div class="stat-label">Mots</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(words)}</div>
                        <div class="stat-label">Word Boost</div>
                    </div>
                </div>
                <div class="section-title">Récent</div>
                <div class="history-list">{recent_html}</div>
            </div>
            <div id="page-dictionary" class="page">
                <div class="page-title">Dictionary</div>
                <div class="page-subtitle">Mots à reconnaître en priorité par Whisper</div>
                <div class="input-row">
                    <input type="text" id="word-input" placeholder="Ajouter un mot..." onkeypress="if(event.key==='Enter')addWord()">
                    <button class="btn-primary" onclick="addWord()">Ajouter</button>
                </div>
                <div class="words-grid">{words_html}</div>
            </div>
            <div id="page-history" class="page">
                <div class="page-title">History</div>
                <div class="page-subtitle">Cliquez pour copier une transcription</div>
                <div id="full-history">{history_html}</div>
            </div>
        </div>
    </div>
    <div class="toast" id="toast">Copié!</div>
    <script>
        function showPage(pageId, el) {{
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('page-' + pageId).classList.add('active');
            if (el) el.classList.add('active');
        }}
        function addWord() {{
            const input = document.getElementById('word-input');
            const word = input.value.trim();
            if (word) {{
                fetch('/api/add/' + encodeURIComponent(word)).then(() => location.reload());
            }}
        }}
        function removeWord(word) {{
            fetch('/api/remove/' + encodeURIComponent(word)).then(() => location.reload());
        }}
        function copyText(text) {{
            navigator.clipboard.writeText(text).then(() => {{
                const toast = document.getElementById('toast');
                toast.textContent = '✓ Copié dans le presse-papier';
                toast.classList.add('show', 'success');
                setTimeout(() => toast.classList.remove('show', 'success'), 2000);
            }});
        }}
    </script>
</body>
</html>'''


class LexiaStreamWindow:
    """Interface Lexia Stream via navigateur."""
    
    @classmethod
    def show_window(cls):
        """Ouvre l'interface dans le navigateur."""
        LexiaStreamServer.start()
        webbrowser.open(f'http://localhost:{LexiaStreamServer._port}')
        print("🌐 Interface ouverte dans le navigateur")


# Alias
SettingsWindow = LexiaStreamWindow


class Pill(QWidget):
    def __init__(self):
        super().__init__()
        self.rec = AudioRecorder()
        self.recording = False
        self.processing = False
        self.bars = [0.0] * 6  # 6 barres fines
        self.text = ""
        self._drag = None
        
        # Animation d'apparition
        self.visibility = 0.0  # 0 = ligne fine, 1 = pilule complète
        self.target_visibility = 0.0
        
        # Dimensions animées - ligne ultra fine au repos
        self.current_width = 30.0   # Très petit au repos
        self.current_height = 3.0   # Ultra fin
        self.target_width = 30.0
        self.target_height = 3.0
        
        # Historique audio pour lissage
        self.audio_history = [0.0] * 4
        
        # Signals for thread-safe hotkey
        self.signals = Signals()
        self.signals.start_recording.connect(self._start_rec)
        self.signals.stop_recording.connect(self._stop_rec)
        self.signals.open_settings.connect(self._open_settings)
        
        # Fenêtre paramètres
        self.settings_window = None
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(100, 36)  # Taille max pour la pilule
        
        # Center bottom
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - 50, screen.bottom() - 50)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)  # ~60fps pour fluidité max
        
        # Setup global hotkey
        if HOTKEY_AVAILABLE:
            self._setup_hotkey()
    
    def _setup_hotkey(self):
        self._down_pressed = False
        self._cmd_held = False
        
        def on_press(key):
            # Track Cmd key
            if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                self._cmd_held = True
            
            # Cmd+↓ = ouvrir paramètres
            if key == keyboard.Key.down and self._cmd_held:
                self.signals.open_settings.emit()
                return
            
            # ↓ seul = enregistrer
            if key == keyboard.Key.down and not self._down_pressed and not self.processing and not self._cmd_held:
                self._down_pressed = True
                self.signals.start_recording.emit()
        
        def on_release(key):
            if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                self._cmd_held = False
            
            if key == keyboard.Key.down and self._down_pressed:
                self._down_pressed = False
                self.signals.stop_recording.emit()
        
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        print("⌨️  ↓ = enregistrer • Cmd+↓ = paramètres")
    
    def _open_settings(self):
        LexiaStreamWindow.show_window()
    
    def _start_rec(self):
        if self.recording or self.processing:
            return
        self.recording = True
        self.rec.start()
        print("🎙️ Recording...")
    
    def _stop_rec(self):
        if not self.recording:
            return
        self.recording = False
        self.processing = True
        path = self.rec.stop()
        
        # Debug: check audio stats
        if path:
            import wave
            with wave.open(path, 'rb') as w:
                frames = w.getnframes()
                rate = w.getframerate()
                duration = frames / rate
            
            # Read and check levels
            data = wavfile.read(path)[1]
            max_level = np.abs(data).max()
            avg_level = np.abs(data).mean()
            
            print(f"⏹️ Audio: {duration:.1f}s, max={max_level}, avg={avg_level:.0f}")
            
            if max_level < 500:
                print("⚠️  ATTENTION: Audio très faible! Vérifie ton micro.")
            
            threading.Thread(target=self.transcribe, args=(path,), daemon=True).start()
        else:
            print("❌ Pas d'audio enregistré")
            self.processing = False
    
    def tick(self):
        # Animation de visibilité et taille
        if self.recording:
            self.target_visibility = 1.0
            self.target_width = 100.0
            self.target_height = 36.0
        elif self.processing:
            self.target_visibility = 0.9
            self.target_width = 90.0
            self.target_height = 32.0
        else:
            self.target_visibility = 0.0
            self.target_width = 30.0   # Ligne ultra fine
            self.target_height = 3.0   # Presque invisible
        
        # Interpolation douce
        self.visibility += (self.target_visibility - self.visibility) * 0.12
        self.current_width += (self.target_width - self.current_width) * 0.15
        self.current_height += (self.target_height - self.current_height) * 0.15
        
        # Animation des barres
        if self.recording:
            # Lissage de l'audio pour fluidité
            current_level = self.rec.level
            self.audio_history = self.audio_history[1:] + [current_level]
            smooth_level = sum(self.audio_history) / len(self.audio_history)
            
            # Barres très réactives avec variation par barre
            for i in range(len(self.bars)):
                # Chaque barre réagit légèrement différemment
                variation = 0.15 * math.sin(time.time() * 12 + i * 1.2)
                target = 0.2 + smooth_level * 0.8 + variation
                self.bars[i] += (target - self.bars[i]) * 0.3  # Interpolation rapide
        elif self.processing:
            # Ondulation douce
            t = time.time() * 4
            for i in range(len(self.bars)):
                target = 0.3 + 0.3 * math.sin(t + i * 1.0)
                self.bars[i] += (target - self.bars[i]) * 0.1
        else:
            # Retour au calme
            for i in range(len(self.bars)):
                self.bars[i] += (0.0 - self.bars[i]) * 0.15
        
        self.update()
    
    def paintEvent(self, e):
        from PyQt6.QtGui import QLinearGradient
        
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dimensions animées
        win_w, win_h = self.width(), self.height()
        w = self.current_width
        h = self.current_height
        v = self.visibility
        
        # Centrer la forme dans la fenêtre
        x_offset = (win_w - w) / 2
        y_offset = (win_h - h) / 2
        
        # Opacité: presque invisible au repos, pilule visible quand actif
        base_alpha = int(15 + v * 225)  # 15 au repos (~6%), 240 actif
        
        # Gradient DA: violet foncé -> rouge foncé -> orange foncé
        grad = QLinearGradient(x_offset, 0, x_offset + w, 0)
        grad.setColorAt(0, QColor(45, 35, 80, base_alpha))
        grad.setColorAt(0.5, QColor(100, 25, 25, base_alpha))
        grad.setColorAt(1, QColor(130, 50, 20, base_alpha))
        
        # Dessiner la pilule/ligne
        path = QPainterPath()
        radius = min(h/2, w/4)
        path.addRoundedRect(x_offset, y_offset, w, h, radius, radius)
        p.fillPath(path, grad)
        
        # Bordure subtile (visible seulement quand actif)
        if v > 0.2:
            border_alpha = int((v - 0.2) * 60)
            p.setPen(QColor(255, 255, 255, border_alpha))
            p.drawPath(path)
        
        # Barres de waveform - seulement quand assez visible
        if v > 0.3 and h > 15:
            bw, gap = 3, 2
            num_bars = len(self.bars)
            tw = num_bars * (bw + gap) - gap
            sx = x_offset + (w - tw) / 2
            
            for i, lv in enumerate(self.bars):
                bx = sx + i * (bw + gap)
                bh = max(2, lv * (h - 10))
                by = y_offset + (h - bh) / 2
                
                bar_alpha = int((v - 0.3) * 1.4 * (150 + lv * 105))
                p.setBrush(QColor(255, 255, 255, min(255, bar_alpha)))
                p.setPen(Qt.PenStyle.NoPen)
                
                bp = QPainterPath()
                bp.addRoundedRect(bx, by, bw, bh, bw/2, bw/2)
                p.drawPath(bp)
    
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._moved = False
            if not self.processing:
                self._start_rec()
    
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.recording:
            if not self._moved:
                self._stop_rec()
            else:
                self.recording = False
                self.rec.stop()
        self._drag = None
    
    def mouseMoveEvent(self, e):
        if self._drag and e.buttons() == Qt.MouseButton.LeftButton:
            delta = e.globalPosition().toPoint() - self.frameGeometry().topLeft() - self._drag
            if delta.manhattanLength() > 10:
                self._moved = True
                self.move(e.globalPosition().toPoint() - self._drag)
    
    def contextMenuEvent(self, e):
        m = QMenu(self)
        if self.text:
            m.addAction(f"📋 {self.text[:25]}...", lambda: pyperclip.copy(self.text) if PASTE_AVAILABLE else None)
            m.addSeparator()
        m.addAction("❌ Quitter", QApplication.quit)
        m.exec(e.globalPos())
    
    def transcribe(self, path):
        try:
            # 1. Transcription avec Word Boost
            word_boost = storage.get_word_boost()
            
            with open(path, 'rb') as f:
                data = {}
                if word_boost:
                    data['word_boost_words'] = ','.join(word_boost)
                r = requests.post(
                    f"{BACKEND_URL}/transcribe",
                    files={'audio': ('audio.wav', f, 'audio/wav')},
                    data=data,
                    timeout=60
                )
            os.unlink(path)
            
            if r.ok:
                raw_text = r.json().get('text', '').strip()
                
                if raw_text:
                    print(f"📝 Brut: {raw_text[:50]}...")
                    
                    # 2. Reformatage intelligent avec SLM + Word Boost context
                    try:
                        boost_words = storage.get_word_boost()
                        reformat_r = requests.post(
                            f"{BACKEND_URL}/reformat",
                            json={
                                "text": raw_text,
                                "word_boost_words": boost_words  # Envoie le contexte au LLM
                            },
                            timeout=30
                        )
                        if reformat_r.ok:
                            result = reformat_r.json()
                            self.text = result.get('formatted', raw_text)
                            text_type = result.get('type', 'text')
                            print(f"✨ Reformaté ({text_type}) avec {len(boost_words)} mots de contexte")
                        else:
                            self.text = raw_text
                    except:
                        self.text = raw_text
                    
                    # 3. Sauvegarder dans l'historique
                    storage.add_to_history(self.text)
                    
                    # 4. Streaming typing - tape caractère par caractère très vite
                    if kb_controller:
                        print(f"⌨️ Streaming: ", end="", flush=True)
                        for char in self.text:
                            kb_controller.type(char)
                            time.sleep(0.008)
                        print(f" ✅")
                    elif PASTE_AVAILABLE:
                        pyperclip.copy(self.text)
                        print(f"✅ Copié: {self.text[:80]}...")
                else:
                    print("⚠️ Transcription vide")
        except Exception as ex:
            print(f"❌ {ex}")
        self.processing = False
    
    def closeEvent(self, e):
        if HOTKEY_AVAILABLE and hasattr(self, 'listener'):
            self.listener.stop()
        e.accept()


if __name__ == "__main__":
    print("=" * 40)
    print("🎤 WHISPER FLOW")
    print("=" * 40)
    print("")
    print("⌨️  Maintenir ↓ (flèche bas) = Enregistrer")
    print("🖱️  Ou cliquer sur la pilule")
    print("📋 Le texte est copié automatiquement")
    print("")
    
    app = QApplication(sys.argv)
    w = Pill()
    w.show()
    sys.exit(app.exec())
