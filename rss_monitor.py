#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Monitor con supporto per CHAT MULTIPLE
Invia notifiche a più persone/gruppi contemporaneamente
"""

import requests
import feedparser
import json
import os
import sys
import time
from datetime import datetime, timedelta
import re
import hashlib

# ================================
# CONFIGURAZIONE MULTI-CHAT
# ================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# CHAT IDS - Aggiungi tutti i destinatari qui
# Formato: lista separata da virgole o variabile d'ambiente
TELEGRAM_CHAT_IDS = "-4942650093"

# In alternativa, puoi definirli direttamente nel codice:
# TELEGRAM_CHAT_IDS = [
#     "123456789",      # Tuo ID personale
#     "-1001234567890", # ID del gruppo
#     "@canale_pubblico" # Username del canale
# ]

# Filtra chat vuote
TELEGRAM_CHAT_IDS = [chat_id.strip() for chat_id in TELEGRAM_CHAT_IDS if chat_id.strip()]

PERSONAL_TOKEN = os.getenv("PERSONAL_TOKEN", "")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
FILE_VISTI = "visti.json"

# ================================
# FEED DA MONITORARE
# ================================

FEEDS_DA_MONITORARE = [
    {
        "name": "Bellucci News",
        "emoji": "📢",
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/16829576264885656380",
        "type": "rss",
        "chat_filter": []  # Vuoto = invia a tutti, altrimenti specifica chat IDs
    },
    {
        "name": "Ministero Updates",
        "emoji": "🚀", 
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/16156285375326995850",
        "type": "rss",
        "chat_filter": []  # Es: ["123456789"] per inviare solo a una persona
    },
    {
        "name": "Bellucci Research",
        "emoji": "🔬",
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/1110300614940787881",
        "type": "rss",
        "chat_filter": []
    }
]

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml',
}

# ================================
# FUNZIONI TELEGRAM MULTI-CHAT
# ================================

def invia_messaggio_telegram(messaggio, chat_id=None, silent=False):
    """
    Invia messaggio a una chat specifica o a tutte le chat configurate.
    
    Args:
        messaggio: Testo da inviare
        chat_id: ID specifico (None = invia a tutti)
        silent: Notifica silenziosa
    """
    if not TELEGRAM_TOKEN:
        log_message("❌ Token Telegram non configurato", "ERROR")
        return False
    
    # Determina a quali chat inviare
    destinatari = [chat_id] if chat_id else TELEGRAM_CHAT_IDS
    
    if not destinatari:
        log_message("❌ Nessuna chat configurata", "ERROR")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    successi = 0
    
    for dest_chat_id in destinatari:
        payload = {
            'chat_id': dest_chat_id,
            'text': messaggio,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False,
            'disable_notification': silent
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30)
            
            if response.status_code == 200:
                successi += 1
                log_message(f"✅ Inviato a chat {dest_chat_id}")
            elif response.status_code == 403:
                log_message(f"⚠️ Chat {dest_chat_id}: Bot bloccato o rimosso", "WARN")
            elif response.status_code == 400:
                error_data = response.json()
                log_message(f"❌ Chat {dest_chat_id}: {error_data.get('description', 'Errore')}", "ERROR")
            else:
                log_message(f"❌ Chat {dest_chat_id}: HTTP {response.status_code}", "ERROR")
                
        except requests.exceptions.RequestException as e:
            log_message(f"❌ Errore invio a {dest_chat_id}: {e}", "ERROR")
        
        time.sleep(0.5)  # Pausa tra invii per evitare rate limit
    
    return successi > 0

def invia_broadcast(messaggio, silent=False):
    """Invia un messaggio a TUTTE le chat configurate."""
    return invia_messaggio_telegram(messaggio, chat_id=None, silent=silent)

def ottieni_info_chat():
    """Ottiene informazioni sulle chat configurate."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_IDS:
        return []
    
    info_chats = []
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
    
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            response = requests.get(url, params={'chat_id': chat_id}, timeout=10)
            if response.status_code == 200:
                data = response.json()['result']
                info = {
                    'chat_id': chat_id,
                    'type': data.get('type', 'unknown'),
                    'title': data.get('title', data.get('first_name', 'N/A')),
                    'username': data.get('username', ''),
                }
                info_chats.append(info)
            else:
                info_chats.append({
                    'chat_id': chat_id,
                    'type': 'unknown',
                    'title': 'Inaccessibile',
                    'error': response.status_code
                })
        except Exception as e:
            log_message(f"⚠️ Errore info chat {chat_id}: {e}")
            info_chats.append({
                'chat_id': chat_id,
                'error': str(e)
            })
    
    return info_chats

# ================================
# FUNZIONI UTILITY
# ================================

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def verifica_configurazione():
    errori = []
    
    if not TELEGRAM_TOKEN:
        errori.append("TELEGRAM_TOKEN mancante")
    if not TELEGRAM_CHAT_IDS or len(TELEGRAM_CHAT_IDS) == 0:
        errori.append("TELEGRAM_CHAT_IDS mancante o vuoto")
    
    if errori:
        log_message("❌ ERRORI DI CONFIGURAZIONE:", "ERROR")
        for errore in errori:
            log_message(f"   - {errore}", "ERROR")
        log_message("\n🔧 Configurazione richiesta:", "INFO")
        log_message("   1. TELEGRAM_TOKEN = token del tuo bot", "INFO")
        log_message("   2. TELEGRAM_CHAT_IDS = chat1,chat2,chat3", "INFO")
        return False
    
    return True

def mostra_configurazione():
    """Mostra la configurazione attuale delle chat."""
    log_message("=" * 60)
    log_message("📱 CONFIGURAZIONE CHAT")
    log_message("=" * 60)
    
    if not TELEGRAM_CHAT_IDS:
        log_message("⚠️ Nessuna chat configurata!")
        return
    
    log_message(f"📊 Totale chat configurate: {len(TELEGRAM_CHAT_IDS)}")
    
    # Ottieni info dettagliate
    info_chats = ottieni_info_chat()
    
    for i, info in enumerate(info_chats, 1):
        log_message(f"\n{i}. Chat ID: {info['chat_id']}")
        log_message(f"   Tipo: {info.get('type', 'N/A')}")
        log_message(f"   Nome: {info.get('title', 'N/A')}")
        if info.get('username'):
            log_message(f"   Username: @{info['username']}")
        if info.get('error'):
            log_message(f"   ⚠️ Errore: {info['error']}", "WARN")
    
    log_message("=" * 60)

def normalizza_url(url):
    import urllib.parse as urlparse
    try:
        parsed = urlparse.urlparse(url)
        query = urlparse.parse_qs(parsed.query)
        parametri_da_rimuovere = [
            'utm_source', 'utm_medium', 'utm_campaign', 'fbclid', '_ga',
            'timestamp', 'time', 'random', 'cache', 'v'
        ]
        for param in parametri_da_rimuovere:
            query.pop(param, None)
        clean_query = urlparse.urlencode(query, doseq=True)
        clean_url = urlparse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, clean_query, parsed.fragment
        ))
        return clean_url
    except:
        return url

def genera_fingerprint(titolo, url):
    try:
        url_pulito = normalizza_url(url)
        titolo_pulito = re.sub(r'[^\w\s]', ' ', titolo.lower().strip())
        titolo_pulito = re.sub(r'\s+', ' ', titolo_pulito)
        contenuto = f"{titolo_pulito}|{url_pulito}"
        fingerprint = hashlib.md5(contenuto.encode('utf-8')).hexdigest()[:12]
        return fingerprint
    except Exception as e:
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:12]

def carica_link_visti():
    if not os.path.exists(FILE_VISTI):
        return set()
    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('fingerprints_visti', []))
    except:
        return set()

def salva_link_visti(fingerprints_visti):
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_fingerprints': len(fingerprints_visti),
            'fingerprints_visti': sorted(list(fingerprints_visti)),
            'versione': '2.3_multi_chat'
        }
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log_message(f"❌ Errore salvataggio: {e}", "ERROR")
        return False

def controlla_feed(feed_info, fingerprints_visti):
    nuovi_contenuti = []
    try:
        log_message(f"🔍 Controllo: {feed_info['name']}")
        
        response = requests.get(feed_info['url'], headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            return nuovi_contenuti
        
        filtro_temporale = datetime.now() - timedelta(days=2)
        primo_avvio = len(fingerprints_visti) <= 1
        
        entries_sorted = sorted(feed.entries, 
                              key=lambda x: getattr(x, 'published_parsed', (1970, 1, 1, 0, 0, 0, 0, 0, 0)), 
                              reverse=True)
        
        for entry in entries_sorted[:5 if not primo_avvio else 1]:
            link = getattr(entry, 'link', '').strip()
            titolo = getattr(entry, 'title', 'Senza titolo').strip()
            
            if not link:
                continue
            
            fingerprint = genera_fingerprint(titolo, link)
            
            if fingerprint in fingerprints_visti:
                continue
            
            pub_date = getattr(entry, 'published_parsed', None)
            if pub_date:
                entry_date = datetime(*pub_date[:6])
                if entry_date < filtro_temporale:
                    continue
            
            messaggio = (
                f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                f"📰 {titolo}\n\n"
                f"🔗 {link}"
            )
            
            if pub_date:
                data_pub = datetime(*pub_date[:6]).strftime("%d/%m/%Y %H:%M")
                messaggio += f"\n📅 {data_pub}"
            
            nuovi_contenuti.append({
                'fingerprint': fingerprint,
                'messaggio': messaggio,
                'chat_filter': feed_info.get('chat_filter', [])
            })
            fingerprints_visti.add(fingerprint)
        
        log_message(f"🆕 {len(nuovi_contenuti)} nuovi in {feed_info['name']}")
        
    except Exception as e:
        log_message(f"❌ Errore {feed_info['name']}: {e}", "ERROR")
    
    return nuovi_contenuti

# ================================
# MAIN
# ================================

def main():
    log_message("=" * 60)
    log_message("🤖 RSS MONITOR v2.3 - MULTI-CHAT")
    log_message("=" * 60)
    
    if not verifica_configurazione():
        sys.exit(1)
    
    mostra_configurazione()
    
    if TEST_MODE:
        log_message("🧪 Modalità test - invio messaggio di prova...")
        invia_broadcast("🧪 <b>Test RSS Monitor Multi-Chat</b>\n\n✅ Configurazione OK!")
        return
    
    fingerprints_visti = carica_link_visti()
    
    tutti_i_contenuti = []
    for feed_info in FEEDS_DA_MONITORARE:
        nuovi = controlla_feed(feed_info, fingerprints_visti)
        tutti_i_contenuti.extend(nuovi)
    
    if not tutti_i_contenuti:
        log_message("📭 Nessun nuovo contenuto")
        salva_link_visti(fingerprints_visti)
        return
    
    log_message(f"📤 Invio {len(tutti_i_contenuti)} contenuti a {len(TELEGRAM_CHAT_IDS)} chat...")
    
    for contenuto in tutti_i_contenuti:
        chat_filter = contenuto.get('chat_filter', [])
        
        if chat_filter:
            # Invia solo a chat specifiche
            for chat_id in chat_filter:
                invia_messaggio_telegram(contenuto['messaggio'], chat_id=chat_id)
        else:
            # Invia a tutte le chat
            invia_broadcast(contenuto['messaggio'])
        
        time.sleep(2)
    
    salva_link_visti(fingerprints_visti)
    log_message(f"✅ Completato: {len(tutti_i_contenuti)} contenuti inviati")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("⏹️ Interruzione manuale")
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 Errore: {e}", "ERROR")
        sys.exit(1)
