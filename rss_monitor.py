#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Feed Monitor - VERSIONE FINALE HARDCODED
Configurazione: Token e Chat ID sono dentro il codice
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
# ⚠️ CONFIGURAZIONE HARDCODED ⚠️
# ================================

TELEGRAM_TOKEN = "8358394281:AAHUUZeDWKSTpu0IP1dnYUanuvlwpiLRSNA"
TELEGRAM_CHAT_ID = "-4942650093"

# Opzionali (per GitHub Gist se configurato)
PERSONAL_TOKEN = os.getenv("PERSONAL_TOKEN", "")
GIST_ID = os.getenv("GIST_ID", "")
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml',
    'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
}

INSTAGRAM_RSS_SERVICES = [
    {
        "name": "Proxigram",
        "instances": [
            "https://proxigram.com",
            "https://proxigram.lunar.icu",
            "https://ig.smnz.de"
        ]
    },
    {
        "name": "RSSHub",
        "instances": [
            "https://rsshub.app",
            "https://rss.shab.fun",
            "https://rsshub.ktachibana.party"
        ]
    }
]

# ================================
# FUNZIONI BASE
# ================================

def log_message(message, level="INFO"):
    """Stampa log con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def verifica_configurazione():
    """Verifica che token e chat ID siano configurati."""
    if not TELEGRAM_TOKEN:
        log_message("❌ TELEGRAM_TOKEN non configurato!", "ERROR")
        return False
    if not TELEGRAM_CHAT_ID:
        log_message("❌ TELEGRAM_CHAT_ID non configurato!", "ERROR")
        return False
    
    log_message(f"✅ Token configurato: {TELEGRAM_TOKEN[:15]}...")
    log_message(f"✅ Chat ID: {TELEGRAM_CHAT_ID}")
    return True

# ================================
# FUNZIONI INSTAGRAM
# ================================

def trova_feed_instagram_funzionante(username, rss_app_id=None):
    """Cerca automaticamente un feed Instagram funzionante."""
    log_message(f"🔍 Cerco feed Instagram per @{username}...")
    
    urls_da_testare = []
    
    # Prova RSS.app se configurato
    if rss_app_id:
        url = f"https://rss.app/feeds/{rss_app_id}.xml"
        urls_da_testare.append(("RSS.app", url))
    
    # Prova Proxigram
    for instance in INSTAGRAM_RSS_SERVICES[0]["instances"]:
        url = f"{instance}/rss/{username}"
        urls_da_testare.append(("Proxigram", url))
    
    # Prova RSSHub
    for instance in INSTAGRAM_RSS_SERVICES[1]["instances"]:
        url = f"{instance}/instagram/user/{username}"
        urls_da_testare.append(("RSSHub", url))
    
    # Testa gli URL
    for servizio, url in urls_da_testare:
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries and len(feed.entries) > 0:
                    log_message(f"   ✅ {servizio} funziona!")
                    return url
        except:
            pass
        time.sleep(0.5)
    
    log_message(f"   ❌ Nessun feed trovato per @{username}")
    return None

def prepara_feeds_instagram():
    """Prepara i feed Instagram cercando URL funzionanti."""
    log_message("🔧 Preparazione feed Instagram...")
    
    for feed in FEEDS_DA_MONITORARE:
        if feed.get('type') == 'instagram_auto':
            username = feed.get('instagram_username')
            rss_app_id = feed.get('rss_app_id')
            
            if username:
                url = trova_feed_instagram_funzionante(username, rss_app_id)
                if url:
                    feed['url'] = url
                    feed['type'] = 'instagram_working'
                    log_message(f"✅ {feed['name']}: configurato")
                else:
                    feed['type'] = 'instagram_broken'
                    log_message(f"❌ {feed['name']}: non disponibile")

# ================================
# FUNZIONI ANTI-DUPLICATI
# ================================

def normalizza_url(url):
    """Rimuove parametri tracking dall'URL."""
    try:
        parsed = urlparse.urlparse(url)
        query = urlparse.parse_qs(parsed.query)
        
        parametri_da_rimuovere = [
            'utm_source', 'utm_medium', 'utm_campaign', 'fbclid', 
            '_ga', 'timestamp', 'cache', 'v'
        ]
        
        for param in parametri_da_rimuovere:
            query.pop(param, None)
        
        clean_query = urlparse.urlencode(query, doseq=True)
        return urlparse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, clean_query, parsed.fragment
        ))
    except:
        return url

def normalizza_titolo_instagram(titolo):
    """Normalizza titolo Instagram."""
    if not titolo:
        return ""
    titolo = titolo.lower().strip()
    titolo = re.sub(r'[^\w\s\-_.,!?]', ' ', titolo)
    titolo = re.sub(r'\s+', ' ', titolo).strip()
    return titolo[:100]

def estrai_id_instagram_da_url(url):
    """Estrae ID post Instagram dall'URL."""
    patterns = [
        r'/p/([A-Za-z0-9_-]+)/',
        r'instagram\.com/p/([A-Za-z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def genera_fingerprint(titolo, url, feed_type="rss"):
    """Genera fingerprint unico per identificare contenuti."""
    try:
        if 'instagram' in feed_type:
            post_id = estrai_id_instagram_da_url(url)
            if post_id:
                return f"ig_{post_id}"
            
            url_pulito = normalizza_url(url)
            titolo_pulito = normalizza_titolo_instagram(titolo)
            contenuto = f"{titolo_pulito}|{url_pulito}" if titolo_pulito else url_pulito
            return f"ig_{hashlib.sha256(contenuto.encode('utf-8')).hexdigest()[:16]}"
        
        url_pulito = normalizza_url(url)
        titolo_pulito = re.sub(r'[^\w\s]', ' ', titolo.lower().strip())
        titolo_pulito = re.sub(r'\s+', ' ', titolo_pulito)
        contenuto = f"{titolo_pulito}|{url_pulito}"
        return hashlib.md5(contenuto.encode('utf-8')).hexdigest()[:12]
    except:
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:12]

# ================================
# GESTIONE STATO
# ================================

def carica_link_visti():
    """Carica fingerprints già visti."""
    # Prova da Gist se configurato
    if PERSONAL_TOKEN and GIST_ID:
        fps = carica_da_gist()
        if fps:
            return fps
    
    # Carica da file locale
    if not os.path.exists(FILE_VISTI):
        log_message("📁 Primo avvio - nessun dato precedente")
        return set()
    
    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            data = json.load(f)
            fps = set(data.get('fingerprints_visti', []))
            log_message(f"📂 Caricati {len(fps)} fingerprints")
            return fps
    except Exception as e:
        log_message(f"⚠️ Errore lettura file: {e}")
        return set()

def salva_link_visti(fingerprints_visti):
    """Salva fingerprints visti."""
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_fingerprints': len(fingerprints_visti),
            'fingerprints_visti': sorted(list(fingerprints_visti)),
            'versione': '2.3_finale_hardcoded'
        }
        
        # Salva su Gist se configurato
        if PERSONAL_TOKEN and GIST_ID:
            salva_su_gist(data)
        
        # Salva locale
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        log_message(f"💾 Salvati {len(fingerprints_visti)} fingerprints")
        return True
    except Exception as e:
        log_message(f"❌ Errore salvataggio: {e}", "ERROR")
        return False

def carica_da_gist():
    """Carica da GitHub Gist."""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {'Authorization': f'token {PERSONAL_TOKEN}'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.json()['files']['visti.json']['content']
            data = json.loads(content)
            fps = set(data.get('fingerprints_visti', []))
            log_message(f"☁️ Caricati {len(fps)} da Gist")
            return fps
    except:
        pass
    return set()

def salva_su_gist(data):
    """Salva su GitHub Gist."""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {'Authorization': f'token {PERSONAL_TOKEN}'}
        payload = {
            'files': {
                'visti.json': {
                    'content': json.dumps(data, ensure_ascii=False, indent=2)
                }
            }
        }
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            log_message("☁️ Sincronizzato con Gist")
    except:
        pass

# ================================
# TELEGRAM
# ================================

def invia_messaggio_telegram(messaggio):
    """Invia messaggio su Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("❌ Token o Chat ID mancante", "ERROR")
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
        if response.status_code == 200:
            return True
        else:
            log_message(f"❌ Telegram errore: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log_message(f"❌ Errore invio: {e}", "ERROR")
        return False

# ================================
# CONTROLLO FEED
# ================================

def controlla_feed(feed_info, fingerprints_visti):
    """Controlla un feed per nuovi contenuti."""
    nuovi_contenuti = []
    
    # Salta feed Instagram non funzionanti
    if feed_info.get('type') == 'instagram_broken':
        log_message(f"⏭️ Skip {feed_info['name']}: feed non disponibile")
        return nuovi_contenuti
    
    try:
        log_message(f"🔍 Controllo: {feed_info['name']}")
        
        if not feed_info.get('url'):
            log_message(f"⚠️ URL mancante per {feed_info['name']}")
            return nuovi_contenuti
        
        # Richiedi feed
        response = requests.get(feed_info['url'], headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            log_message(f"📭 Nessun contenuto in {feed_info['name']}")
            return nuovi_contenuti
        
        feed_type = feed_info.get('type', 'rss')
        giorni_filtro = 3 if 'instagram' in feed_type else 2
        filtro_temporale = datetime.now() - timedelta(days=giorni_filtro)
        primo_avvio = len(fingerprints_visti) <= 1
        
        # Ordina per data
        entries_sorted = sorted(
            feed.entries,
            key=lambda x: getattr(x, 'published_parsed', (1970, 1, 1, 0, 0, 0, 0, 0, 0)),
            reverse=True
        )
        
        # Limita numero elementi da processare
        limite = 5 if not primo_avvio else 2
        
        for entry in entries_sorted[:limite]:
            link = getattr(entry, 'link', '').strip()
            titolo = getattr(entry, 'title', 'Senza titolo').strip()
            
            if not link:
                continue
            
            # Genera fingerprint
            fingerprint = genera_fingerprint(titolo, link, feed_type)
            
            # Controlla se già visto
            if fingerprint in fingerprints_visti:
                continue
            
            # Controlla data
            pub_date = getattr(entry, 'published_parsed', None)
            if pub_date:
                entry_date = datetime(*pub_date[:6])
                if entry_date < filtro_temporale:
                    continue
            
            # Crea messaggio
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
                'messaggio': messaggio
            })
            fingerprints_visti.add(fingerprint)
        
        if nuovi_contenuti:
            log_message(f"🆕 {len(nuovi_contenuti)} nuovi in {feed_info['name']}")
        
    except Exception as e:
        log_message(f"❌ Errore in {feed_info['name']}: {e}", "ERROR")
    
    return nuovi_contenuti

# ================================
# MAIN
# ================================

def main():
    log_message("=" * 60)
    log_message("🤖 RSS MONITOR v2.3 - FINALE HARDCODED")
    log_message("=" * 60)
    log_message(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message("-" * 60)
    
    # Verifica configurazione
    if not verifica_configurazione():
        sys.exit(1)
    
    # Prepara feed Instagram
    prepara_feeds_instagram()
    
    # Modalità test
    if TEST_MODE:
        log_message("🧪 Modalità TEST attivata")
        invia_messaggio_telegram(
            "🧪 <b>Test RSS Monitor</b>\n\n"
            "✅ Configurazione OK!\n"
            f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        log_message("✅ Test completato")
        return
    
    # Carica stato
    fingerprints_visti = carica_link_visti()
    
    # Controlla tutti i feed
    tutti_i_contenuti = []
    for feed_info in FEEDS_DA_MONITORARE:
        nuovi = controlla_feed(feed_info, fingerprints_visti)
        tutti_i_contenuti.extend(nuovi)
    
    # Se non ci sono novità
    if not tutti_i_contenuti:
        log_message("📭 Nessun nuovo contenuto trovato")
        salva_link_visti(fingerprints_visti)
        log_message("=" * 60)
        return
    
    # Invia messaggi
    log_message(f"📤 Invio {len(tutti_i_contenuti)} messaggi...")
    messaggi_inviati = 0
    
    for contenuto in tutti_i_contenuti:
        if invia_messaggio_telegram(contenuto['messaggio']):
            messaggi_inviati += 1
            log_message(f"✅ Messaggio {messaggi_inviati}/{len(tutti_i_contenuti)} inviato")
        time.sleep(2)  # Pausa tra messaggi
    
    # Salva stato
    salva_link_visti(fingerprints_visti)
    
    # Report finale
    log_message("=" * 60)
    log_message(f"✅ COMPLETATO: {messaggi_inviati} messaggi inviati")
    log_message(f"💾 Totale fingerprints tracciati: {len(fingerprints_visti)}")
    log_message("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("\n⏹️ Interruzione manuale")
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 ERRORE CRITICO: {e}", "ERROR")
        # Tenta di inviare notifica errore
        try:
            invia_messaggio_telegram(
                f"🚨 <b>RSS Monitor - Errore Critico</b>\n\n"
                f"❌ {str(e)}\n"
                f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
        except:
            pass
        sys.exit(1)
