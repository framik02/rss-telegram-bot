#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Feed Monitor - Configurazione Hardcoded
Token: 8358394281:AAHUUZeDWKSTpu0IP1dnYUanuvlwpiLRSNA
Chat ID: -4942650093
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
import urllib.parse as urlparse

# ================================
# CONFIGURAZIONE - DATI HARDCODED
# ================================

TELEGRAM_TOKEN = "8358394281:AAHUUZeDWKSTpu0IP1dnYUanuvlwpiLRSNA"
TELEGRAM_CHAT_ID = "-4942650093"
TELEGRAM_CHAT_IDS = ["-4942650093"]  # Lista per compatibilità multi-chat

PERSONAL_TOKEN = os.getenv("PERSONAL_TOKEN", "")
GIST_ID = os.getenv("GIST_ID", "")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

FILE_VISTI = "visti.json"

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
        "name": "Instagram - Fratelli d'Italia",
        "emoji": "📸",
        "url": "",
        "type": "instagram_auto",
        "instagram_username": "fratelliditalia",
        "rss_app_id": "eSz39hnyubmwLjuW"
    },
    {
        "name": "Instagram - Ministero del Lavoro",
        "emoji": "🚀",
        "url": "",
        "type": "instagram_auto",
        "instagram_username": "minlavoro",
        "rss_app_id": "O2NQW8pvSIQGpkby"
    },
    {
        "name": "Instagram - Meloni",
        "emoji": "📸", 
        "url": "",
        "type": "instagram_auto",
        "instagram_username": "giorgia.meloni",
        "rss_app_id": "opRYqgialL3uzDej"
    }
]

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml',
}

INSTAGRAM_RSS_SERVICES = [
    {"name": "Proxigram", "instances": ["https://proxigram.com", "https://proxigram.lunar.icu", "https://ig.smnz.de"]},
    {"name": "RSSHub", "instances": ["https://rsshub.app", "https://rss.shab.fun", "https://rsshub.ktachibana.party"]},
]

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def verifica_configurazione():
    if not TELEGRAM_TOKEN:
        log_message("❌ TELEGRAM_TOKEN mancante!", "ERROR")
        return False
    if not TELEGRAM_CHAT_ID:
        log_message("❌ TELEGRAM_CHAT_ID mancante!", "ERROR")
        return False
    log_message(f"✅ Token: {TELEGRAM_TOKEN[:10]}...")
    log_message(f"✅ Chat ID: {TELEGRAM_CHAT_ID}")
    return True

def trova_feed_instagram_funzionante(username, rss_app_id=None):
    log_message(f"🔍 Cerco feed per @{username}...")
    urls = []
    
    if rss_app_id:
        urls.append(("RSS.app", f"https://rss.app/feeds/{rss_app_id}.xml"))
    
    for instance in INSTAGRAM_RSS_SERVICES[0]["instances"]:
        urls.append(("Proxigram", f"{instance}/rss/{username}"))
    
    for instance in INSTAGRAM_RSS_SERVICES[1]["instances"]:
        urls.append(("RSSHub", f"{instance}/instagram/user/{username}"))
    
    for servizio, url in urls:
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    log_message(f"   ✅ {servizio} OK!")
                    return url
        except:
            pass
        time.sleep(0.5)
    
    log_message(f"   ❌ Nessun feed trovato")
    return None

def prepara_feeds_instagram():
    log_message("🔧 Setup feed Instagram...")
    for feed in FEEDS_DA_MONITORARE:
        if feed.get('type') == 'instagram_auto':
            url = trova_feed_instagram_funzionante(feed.get('instagram_username'), feed.get('rss_app_id'))
            feed['url'] = url or ""
            feed['type'] = 'instagram_working' if url else 'instagram_broken'

def normalizza_url(url):
    try:
        parsed = urlparse.urlparse(url)
        query = urlparse.parse_qs(parsed.query)
        for p in ['utm_source', 'utm_medium', 'fbclid', '_ga', 'cache', 'v']:
            query.pop(p, None)
        return urlparse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlparse.urlencode(query, doseq=True), parsed.fragment))
    except:
        return url

def normalizza_titolo_instagram(titolo):
    if not titolo:
        return ""
    t = titolo.lower().strip()
    t = re.sub(r'[^\w\s\-_.,!?]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:100]

def estrai_id_instagram(url):
    for pattern in [r'/p/([A-Za-z0-9_-]+)/', r'instagram\.com/p/([A-Za-z0-9_-]+)']:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def genera_fingerprint(titolo, url, feed_type="rss"):
    try:
        if 'instagram' in feed_type:
            post_id = estrai_id_instagram(url)
            if post_id:
                return f"ig_{post_id}"
            url_pulito = normalizza_url(url)
            titolo_pulito = normalizza_titolo_instagram(titolo)
            contenuto = f"{titolo_pulito}|{url_pulito}" if titolo_pulito else url_pulito
            return f"ig_{hashlib.sha256(contenuto.encode('utf-8')).hexdigest()[:16]}"
        url_pulito = normalizza_url(url)
        titolo_pulito = re.sub(r'[^\w\s]', ' ', titolo.lower().strip())
        titolo_pulito = re.sub(r'\s+', ' ', titolo_pulito)
        return hashlib.md5(f"{titolo_pulito}|{url_pulito}".encode('utf-8')).hexdigest()[:12]
    except:
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:12]

def carica_link_visti():
    if PERSONAL_TOKEN and GIST_ID:
        fps = carica_da_gist()
        if fps:
            return fps
    if not os.path.exists(FILE_VISTI):
        log_message("📁 Primo avvio")
        return set()
    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            data = json.load(f)
            fps = set(data.get('fingerprints_visti', []))
            log_message(f"📂 Caricati {len(fps)} fingerprints")
            return fps
    except:
        return set()

def salva_link_visti(fps):
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_fingerprints': len(fps),
            'fingerprints_visti': sorted(list(fps)),
            'versione': '2.3_hardcoded_fix'
        }
        if PERSONAL_TOKEN and GIST_ID:
            salva_su_gist(data)
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log_message(f"❌ Errore salvataggio: {e}", "ERROR")
        return False

def carica_da_gist():
    if not PERSONAL_TOKEN or not GIST_ID:
        return set()
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {'Authorization': f'token {PERSONAL_TOKEN}'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.json()['files']['visti.json']['content']
            fps = set(json.loads(content).get('fingerprints_visti', []))
            log_message(f"☁️ {len(fps)} da Gist")
            return fps
    except:
        pass
    return set()

def salva_su_gist(data):
    if not PERSONAL_TOKEN or not GIST_ID:
        return
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {'Authorization': f'token {PERSONAL_TOKEN}'}
        payload = {'files': {'visti.json': {'content': json.dumps(data, ensure_ascii=False, indent=2)}}}
        requests.patch(url, headers=headers, json=payload, timeout=10)
    except:
        pass

def invia_messaggio_telegram(messaggio):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
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
        return response.status_code == 200
    except Exception as e:
        log_message(f"❌ Errore Telegram: {e}", "ERROR")
        return False

def controlla_feed(feed_info, fps_visti):
    nuovi = []
    if feed_info.get('type') == 'instagram_broken':
        return nuovi
    try:
        log_message(f"🔍 {feed_info['name']}")
        if not feed_info.get('url'):
            return nuovi
        
        response = requests.get(feed_info['url'], headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            return nuovi
        
        feed_type = feed_info.get('type', 'rss')
        filtro = datetime.now() - timedelta(days=3 if 'instagram' in feed_type else 2)
        primo_avvio = len(fps_visti) <= 1
        
        entries = sorted(feed.entries, key=lambda x: getattr(x, 'published_parsed', (1970,1,1,0,0,0,0,0,0)), reverse=True)
        
        for entry in entries[:5 if not primo_avvio else 2]:
            link = getattr(entry, 'link', '').strip()
            titolo = getattr(entry, 'title', 'Senza titolo').strip()
            if not link:
                continue
            
            fingerprint = genera_fingerprint(titolo, link, feed_type)
            if fingerprint in fps_visti:
                continue
            
            pub_date = getattr(entry, 'published_parsed', None)
            if pub_date:
                entry_date = datetime(*pub_date[:6])
                if entry_date < filtro:
                    continue
            
            msg = f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n📰 {titolo}\n\n🔗 {link}"
            if pub_date:
                msg += f"\n📅 {datetime(*pub_date[:6]).strftime('%d/%m/%Y %H:%M')}"
            
            nuovi.append({'fingerprint': fingerprint, 'messaggio': msg})
            fps_visti.add(fingerprint)
        
        log_message(f"🆕 {len(nuovi)} nuovi")
    except Exception as e:
        log_message(f"❌ Errore: {e}", "ERROR")
    return nuovi

def main():
    log_message("="*60)
    log_message("🤖 RSS MONITOR v2.3 - HARDCODED FIX")
    log_message("="*60)
    
    if not verifica_configurazione():
        sys.exit(1)
    
    prepara_feeds_instagram()
    
    if TEST_MODE:
        log_message("🧪 Test mode")
        invia_messaggio_telegram("🧪 <b>RSS Monitor Test</b>\n\n✅ Tutto OK!")
        return
    
    fps = carica_link_visti()
    
    tutti = []
    for feed in FEEDS_DA_MONITORARE:
        tutti.extend(controlla_feed(feed, fps))
    
    if not tutti:
        log_message("📭 Nessun nuovo contenuto")
        salva_link_visti(fps)
        return
    
    log_message(f"📤 Invio {len(tutti)} contenuti...")
    for c in tutti:
        if invia_messaggio_telegram(c['messaggio']):
            log_message(f"✅ Inviato")
        time.sleep(2)
    
    salva_link_visti(fps)
    log_message(f"✅ Fine: {len(tutti)} inviati")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("⏹️ Stop")
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 Errore: {e}", "ERROR")
        invia_messaggio_telegram(f"🚨 <b>Errore RSS Monitor</b>\n\n❌ {str(e)}")
        sys.exit(1)
