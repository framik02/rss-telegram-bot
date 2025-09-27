#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Feed Monitor per GitHub Actions
Versione ottimizzata e pulita
"""

import requests
import feedparser
import json
import os
import sys
import time
from datetime import datetime

# ================================
# CONFIGURAZIONE
# ================================

# Token e Chat ID da GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# File per lo stato
FILE_VISTI = "visti.json"

# Feed da monitorare (personalizza questa lista)
FEEDS_DA_MONITORARE = [
    {
        "name": "Bellucci News",
        "emoji": "📢",
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/16829576264885656380",
        "type": "rss"
    },
    {
        "name": "Ministero Updates",
        "emoji": "🚀", 
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/16156285375326995850",
        "type": "rss"
    },
    {
        "name": "Bellucci Research",
        "emoji": "🔬",
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/1110300614940787881",
        "type": "rss"
    },
    {
        "name": "Instagram - Fratelli d’Italia",
        "emoji": "📸",
        "url": "https://rsshub.app/instagram/user/fratelliditalia",
        "type": "instagram"
    },
    {
        "name": "Instagram - Ministero del Lavoro",
        "emoji": "🚀",
        "url": "https://rsshub.app/instagram/user/minlavoro",
        "type": "instagram"
    },
    {
        "name": "Instagram - National Geographic",
        "emoji": "📸",
        "url": "https://rsshub.app/instagram/user/natgeo",
        "type": "instagram"
    }
]

# Istanze RSSHub per failover
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rss.shab.fun", 
    "https://rsshub.ktachibana.party",
]

# ================================
# FUNZIONI UTILITY
# ================================

def log_message(message, level="INFO"):
    """Stampa messaggi con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def verifica_configurazione():
    """Verifica che la configurazione sia corretta."""
    errori = []
    
    if not TELEGRAM_TOKEN:
        errori.append("TELEGRAM_TOKEN mancante")
    if not TELEGRAM_CHAT_ID:
        errori.append("TELEGRAM_CHAT_ID mancante")
    
    if errori:
        log_message("❌ ERRORI DI CONFIGURAZIONE:", "ERROR")
        for errore in errori:
            log_message(f"   - {errore}", "ERROR")
        log_message("🔧 Aggiungi i secrets su GitHub: TELEGRAM_TOKEN e TELEGRAM_CHAT_ID", "INFO")
        return False
    return True

def carica_link_visti():
    """Carica i link già visti dal file JSON locale."""
    if not os.path.exists(FILE_VISTI):
        log_message(f"📁 File {FILE_VISTI} non trovato - primo avvio")
        return set()
    
    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return set()
            data = json.loads(content)
            links = set(data.get('link_visti', []))
            log_message(f"📂 Caricati {len(links)} link già processati")
            return links
    except Exception as e:
        log_message(f"❌ Errore nel leggere {FILE_VISTI}: {e}", "ERROR")
        return set()

def salva_link_visti(link_visti):
    """Salva i link visti nel file JSON locale."""
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_link': len(link_visti),
            'link_visti': sorted(list(link_visti)),
            'github_action': True,
            'repository': os.getenv('GITHUB_REPOSITORY', 'unknown'),
            'run_id': os.getenv('GITHUB_RUN_ID', 'unknown')
        }
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log_message(f"💾 Salvati {len(link_visti)} link nel file {FILE_VISTI}")
        return True
    except Exception as e:
        log_message(f"❌ Errore nel salvare {FILE_VISTI}: {e}", "ERROR")
        return False

def invia_messaggio_telegram(messaggio):
    """Invia un messaggio su Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("❌ Token Telegram non configurato", "ERROR")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': messaggio,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        log_message("✅ Messaggio inviato su Telegram")
        return True
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Errore nell'invio Telegram: {e}", "ERROR")
        return False

def prova_rsshub_instances(url_originale):
    """Prova diverse istanze RSSHub se quella principale non funziona."""
    for instance in RSSHUB_INSTANCES:
        try:
            if url_originale.startswith("https://rsshub.app"):
                test_url = url_originale.replace("https://rsshub.app", instance)
                response = requests.head(test_url, timeout=10)
                if response.status_code == 200:
                    log_message(f"✅ Istanza RSSHub funzionante: {instance}")
                    return test_url
        except:
            continue
    log_message("⚠️ Nessuna istanza RSSHub disponibile, uso originale")
    return url_originale

def controlla_feed(feed_info, link_visti):
    """Controlla un singolo feed per nuovi contenuti."""
    nuovi_contenuti = []
    try:
        log_message(f"🔍 Controllo {feed_info.get('type', 'rss')}: {feed_info['name']}")
        feed_url = feed_info['url']
        
        # Failover per RSSHub
        if "rsshub.app" in feed_url:
            try:
                test_response = requests.head(feed_url, timeout=10)
                if test_response.status_code != 200:
                    log_message("⚠️ Istanza RSSHub principale non risponde")
                    feed_url = prova_rsshub_instances(feed_url)
            except:
                feed_url = prova_rsshub_instances(feed_url)
        
        response = requests.get(feed_url, timeout=15)
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            log_message(f"📭 Nessun contenuto in {feed_info['name']}")
            return nuovi_contenuti
        
        for entry in feed.entries:
            link = getattr(entry, 'link', '').strip()
            titolo = getattr(entry, 'title', 'Titolo non disponibile').strip()
            if not link or link in link_visti:
                continue
            
            tipo = feed_info.get('type', 'rss')
            messaggio = (
                f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                f"📰 {titolo}\n\n"
                f"🔗 {link}"
            )
            nuovi_contenuti.append({'link': link, 'messaggio': messaggio})
            link_visti.add(link)
        
        log_message(f"🆕 {len(nuovi_contenuti)} nuovi contenuti in {feed_info['name']}")
    except Exception as e:
        log_message(f"❌ Errore nel feed {feed_info['name']}: {e}", "ERROR")
    return nuovi_contenuti

def main():
    log_message("=" * 60)
    log_message("🤖 RSS FEED MONITOR - GitHub Actions")
    log_message("=" * 60)
    log_message(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log_message(f"📋 Monitoraggio {len(FEEDS_DA_MONITORARE)} feed")
    log_message("-" * 60)
    
    if not verifica_configurazione():
        sys.exit(1)
    
    if TEST_MODE:
        log_message("🧪 Modalità test attivata")
        invia_messaggio_telegram("🧪 Test RSS Monitor completato con successo ✅")
        return
    
    link_visti = carica_link_visti()
    nuovi_contenuti_totali = 0
    
    for feed_info in FEEDS_DA_MONITORARE:
        nuovi_contenuti = controlla_feed(feed_info, link_visti)
        for contenuto in nuovi_contenuti:
            if invia_messaggio_telegram(contenuto['messaggio']):
                nuovi_contenuti_totali += 1
                time.sleep(1)
    
    salva_link_visti(link_visti)
    
    log_message("=" * 60)
    log_message(f"📤 {nuovi_contenuti_totali} nuovi contenuti inviati")
    log_message(f"💾 {len(link_visti)} link tracciati")
    log_message("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("⏹️ Interruzione manuale")
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 Errore critico: {e}", "ERROR")
        sys.exit(1)
