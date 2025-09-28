#!/usr/bin/env python3
# -- coding: utf-8 --
"""
RSS Feed Monitor per GitHub Actions
Versione ottimizzata con fix definitivo per duplicati Instagram
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
    # Instagram - Soluzioni alternative
    {
        "name": "Instagram - Fratelli d'Italia",
        "emoji": "📸",
        "url": "https://rss.app/feeds/eSz39hnyubmwLjuW.xml",
        "type": "instagram_alt",
        "backup_urls": [
            "https://rsshub.ktachibana.party/instagram/user/fratelliditalia",
            "https://rss.shab.fun/instagram/user/fratelliditalia"
        ]
    },
    {
        "name": "Instagram - Ministero del Lavoro",
        "emoji": "🚀",
        "url": "https://rss.app/feeds/O2NQW8pvSIQGpkby.xml",
        "type": "instagram_alt",
        "backup_urls": [
            "https://rsshub.ktachibana.party/instagram/user/minlavoro",
            "https://rss.shab.fun/instagram/user/minlavoro"
        ]
    },
    {
        "name": "Instagram - Meloni",
        "emoji": "📸", 
        "url": "https://rss.app/feeds/opRYqgialL3uzDej.xml",
        "type": "instagram_alt",
        "backup_urls": [
            "https://rsshub.ktachibana.party/instagram/user/natgeo",
            "https://rss.shab.fun/instagram/user/natgeo"
        ]
    }
]

# Istanze RSSHub per failover
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rss.shab.fun", 
    "https://rsshub.ktachibana.party",
    "https://rsshub.rssforever.com"
]

# Headers per evitare blocking
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# ================================
# FUNZIONI ANTI-DUPLICATI MIGLIORATE
# ================================

def normalizza_titolo_instagram(titolo):
    """Normalizza il titolo Instagram per evitare variazioni che causano duplicati."""
    if not titolo:
        return ""
    
    # Converti in lowercase
    titolo = titolo.lower().strip()
    
    # Rimuovi emoji e caratteri speciali
    titolo = re.sub(r'[^\w\s\-_.,!?]', ' ', titolo)
    
    # Rimuovi spazi multipli
    titolo = re.sub(r'\s+', ' ', titolo).strip()
    
    # Rimuovi pattern comuni che variano
    titolo = re.sub(r'\b(new|updated|latest|today|now)\b', '', titolo)
    
    # Rimuovi date e timestamp che possono variare
    titolo = re.sub(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', '', titolo)
    titolo = re.sub(r'\d{1,2}:\d{2}', '', titolo)
    
    # Tronca se troppo lungo (prendi solo i primi 100 caratteri significativi)
    titolo = titolo[:100].strip()
    
    return titolo

def estrai_id_instagram_da_url(url):
    """Estrae l'ID del post Instagram dall'URL se possibile."""
    try:
        # Pattern per ID Instagram
        patterns = [
            r'/p/([A-Za-z0-9_-]+)/',
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            r'&id=([A-Za-z0-9_-]+)',
            r'post_id=([A-Za-z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Fallback: usa la parte finale dell'URL
        parsed = urlparse.urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        if path_parts:
            return path_parts[-1]
            
    except:
        pass
    
    return None

def normalizza_url(url):
    """Rimuove parametri casuali dall'URL per evitare duplicati."""
    try:
        parsed = urlparse.urlparse(url)
        query = urlparse.parse_qs(parsed.query)
        
        # Rimuovi parametri tracking che cambiano sempre
        parametri_da_rimuovere = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
            'fbclid', '_ga', 'gclid', 'mc_cid', 'mc_eid', 'ref', 'source',
            '_hsenc', '_hsmi', 'hsCtaTracking', 'mkt_tok', 'trk', 't', 's',
            'timestamp', 'time', 'random', 'nonce', 'cache', 'v'
        ]
        
        for param in parametri_da_rimuovere:
            query.pop(param, None)
        
        # Ricostruisci URL pulito
        clean_query = urlparse.urlencode(query, doseq=True)
        clean_url = urlparse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, clean_query, parsed.fragment
        ))
        return clean_url
    except:
        return url

def genera_fingerprint_instagram(titolo, url, feed_type="rss"):
    """Genera fingerprint specifico per Instagram con logica anti-duplicati avanzata."""
    try:
        # Per Instagram, usa strategie diverse
        if 'instagram' in feed_type:
            # Strategia 1: Prova a estrarre ID del post dall'URL
            post_id = estrai_id_instagram_da_url(url)
            if post_id:
                fingerprint = f"ig_{post_id}"
                return fingerprint
            
            # Strategia 2: Usa URL normalizzato + titolo normalizzato
            url_pulito = normalizza_url(url)
            titolo_pulito = normalizza_titolo_instagram(titolo)
            
            # Se il titolo è troppo generico o vuoto, usa solo URL
            if not titolo_pulito or len(titolo_pulito) < 10:
                contenuto = url_pulito
            else:
                contenuto = f"{titolo_pulito}|{url_pulito}"
            
            # Per Instagram, usa SHA256 per maggiore precisione
            fingerprint = hashlib.sha256(contenuto.encode('utf-8')).hexdigest()[:16]
            return f"ig_{fingerprint}"
        
        # Per feed normali, usa la logica originale
        url_pulito = normalizza_url(url)
        titolo_pulito = re.sub(r'[^\w\s]', ' ', titolo.lower().strip())
        titolo_pulito = re.sub(r'\s+', ' ', titolo_pulito)
        
        contenuto = f"{titolo_pulito}|{url_pulito}"
        fingerprint = hashlib.md5(contenuto.encode('utf-8')).hexdigest()[:12]
        
        return fingerprint
        
    except Exception as e:
        log_message(f"❌ Errore generazione fingerprint: {e}")
        # Fallback sicuro
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:12]

# ================================
# FUNZIONI UTILITY (INVARIATE)
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
    """Carica i fingerprint già visti dal file JSON locale o da GitHub Gist."""
    log_message("🔍 DEBUG: Inizio caricamento fingerprints...")
    
    # Prima prova a caricare da GitHub Gist (persistente)
    fingerprints_da_gist = carica_da_gist()
    if fingerprints_da_gist:
        log_message(f"☁ DEBUG: Caricati {len(fingerprints_da_gist)} da Gist")
        return fingerprints_da_gist
    
    # Se non c'è Gist, prova il file locale
    if not os.path.exists(FILE_VISTI):
        log_message(f"📁 DEBUG: File {FILE_VISTI} non trovato - primo avvio")
        return set()
    
    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            log_message(f"📄 DEBUG: File content length: {len(content)}")
            
            if not content:
                log_message("📄 DEBUG: File vuoto")
                return set()
                
            data = json.loads(content)
            log_message(f"📊 DEBUG: JSON keys: {list(data.keys())}")
            
            # Carica fingerprints
            fingerprints = set(data.get('fingerprints_visti', []))
            log_message(f"🔢 DEBUG: Fingerprints trovati: {len(fingerprints)}")
            
            # Controlla età dei dati e pulisci se troppo vecchi
            ultimo_aggiornamento = data.get('ultimo_aggiornamento', '')
            if ultimo_aggiornamento:
                try:
                    ultima_data = datetime.fromisoformat(ultimo_aggiornamento.replace('Z', '+00:00'))
                    giorni_fa = (datetime.now() - ultima_data.replace(tzinfo=None)).days
                    log_message(f"📅 DEBUG: Dati di {giorni_fa} giorni fa")
                    
                    if giorni_fa > 7:
                        log_message(f"⚠ Dati vecchi di {giorni_fa} giorni - reset parziale")
                        # Per Instagram, mantieni più fingerprints per sicurezza
                        instagram_fps = [fp for fp in fingerprints if fp.startswith('ig_')]
                        altri_fps = [fp for fp in fingerprints if not fp.startswith('ig_')]
                        
                        # Mantieni tutti gli Instagram + ultimi 100 altri
                        fingerprints_puliti = set(instagram_fps + altri_fps[-100:])
                        log_message(f"🗑 DEBUG: Mantenuti {len(instagram_fps)} Instagram + {len(altri_fps[-100:])} altri")
                        return fingerprints_puliti
                except Exception as e:
                    log_message(f"❌ DEBUG: Errore parsing data: {e}")
            
            log_message(f"📂 DEBUG: FINALE - Caricati {len(fingerprints)} fingerprints già processati")
            return fingerprints
            
    except Exception as e:
        log_message(f"❌ DEBUG: Errore nel leggere {FILE_VISTI}: {e}", "ERROR")
        return set()

def salva_link_visti(fingerprints_visti):
    """Salva i fingerprints visti nel file JSON locale con gestione GitHub Gist."""
    log_message(f"💾 DEBUG: Inizio salvataggio {len(fingerprints_visti)} fingerprints...")
    
    try:
        # Conta fingerprints per tipo
        instagram_count = len([fp for fp in fingerprints_visti if fp.startswith('ig_')])
        altri_count = len(fingerprints_visti) - instagram_count
        
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_fingerprints': len(fingerprints_visti),
            'instagram_fingerprints': instagram_count,
            'altri_fingerprints': altri_count,
            'fingerprints_visti': sorted(list(fingerprints_visti)),
            'github_action': True,
            'repository': os.getenv('GITHUB_REPOSITORY', 'unknown'),
            'run_id': os.getenv('GITHUB_RUN_ID', 'unknown'),
            'versione': '2.1_instagram_fix'
        }
        
        # DEBUG: Mostra statistiche
        log_message(f"📊 DEBUG: Instagram FPs: {instagram_count}, Altri FPs: {altri_count}")
        if fingerprints_visti:
            primi_ig = [fp for fp in fingerprints_visti if fp.startswith('ig_')][:3]
            if primi_ig:
                log_message(f"🔍 DEBUG: Primi 3 Instagram FPs: {primi_ig}")
        
        # Salva localmente
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        log_message(f"💾 Salvati {len(fingerprints_visti)} fingerprints nel file {FILE_VISTI}")
        
        # Sincronizza con GitHub Gist
        salva_su_gist(data)
        
        return True
    except Exception as e:
        log_message(f"❌ DEBUG: Errore nel salvare {FILE_VISTI}: {e}", "ERROR")
        return False

def salva_su_gist(data):
    """Salva i dati su GitHub Gist per persistenza tra le esecuzioni."""
    if not GITHUB_TOKEN:
        return
        
    gist_id = os.getenv('GIST_ID', '')
    if not gist_id:
        return
        
    try:
        url = f"https://api.github.com/gists/{gist_id}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'files': {
                'visti.json': {
                    'content': json.dumps(data, ensure_ascii=False, indent=2)
                }
            }
        }
        
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            log_message("☁ Dati sincronizzati con GitHub Gist")
        else:
            log_message(f"⚠ Errore sync Gist: {response.status_code}")
            
    except Exception as e:
        log_message(f"⚠ Errore sincronizzazione Gist: {e}")

def carica_da_gist():
    """Carica i dati da GitHub Gist se disponibile."""
    if not GITHUB_TOKEN:
        return set()
        
    gist_id = os.getenv('GIST_ID', '')
    if not gist_id:
        return set()
        
    try:
        url = f"https://api.github.com/gists/{gist_id}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            gist_data = response.json()
            if 'visti.json' in gist_data['files']:
                content = gist_data['files']['visti.json']['content']
                data = json.loads(content)
                fingerprints = set(data.get('fingerprints_visti', []))
                if fingerprints:
                    log_message(f"☁ Caricati {len(fingerprints)} fingerprints da GitHub Gist")
                    return fingerprints
                
    except Exception as e:
        log_message(f"⚠ Errore caricamento da Gist: {e}")
        
    return set()

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

def testa_url_feed(url, timeout=10):
    """Testa se un URL feed è accessibile."""
    try:
        response = requests.head(url, headers=REQUEST_HEADERS, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def trova_url_funzionante(feed_info):
    """Trova un URL funzionante per il feed."""
    # Prima prova l'URL principale
    if testa_url_feed(feed_info['url']):
        return feed_info['url']
    
    # Se ha URL di backup, provali
    backup_urls = feed_info.get('backup_urls', [])
    for backup_url in backup_urls:
        log_message(f"🔄 Provo URL backup: {backup_url}")
        if testa_url_feed(backup_url):
            log_message(f"✅ URL backup funzionante: {backup_url}")
            return backup_url
    
    # Per RSSHub, prova altre istanze
    if "rsshub" in feed_info['url']:
        return prova_rsshub_instances(feed_info['url'])
    
    log_message(f"⚠ Nessun URL funzionante per {feed_info['name']}")
    return feed_info['url']

def prova_rsshub_instances(url_originale):
    """Prova diverse istanze RSSHub se quella principale non funziona."""
    for instance in RSSHUB_INSTANCES:
        try:
            if "rsshub" in url_originale:
                path_match = re.search(r'rsshub[^/]*/(.+)', url_originale)
                if path_match:
                    path = path_match.group(1)
                    test_url = f"{instance}/{path}"
                    if testa_url_feed(test_url):
                        log_message(f"✅ Istanza RSSHub funzionante: {instance}")
                        return test_url
        except Exception as e:
            log_message(f"❌ Errore testando {instance}: {e}")
            continue
    
    log_message("⚠ Nessuna istanza RSSHub disponibile")
    return url_originale

def pulisci_contenuto_instagram(titolo, link):
    """Pulisce e migliora il contenuto Instagram."""
    titolo_pulito = re.sub(r'[^\w\s\-_.,!?]', '', titolo)
    
    if len(titolo_pulito) > 100:
        titolo_pulito = titolo_pulito[:97] + "..."
    
    return titolo_pulito

def estrai_data_da_messaggio(messaggio):
    """Estrae la data dal messaggio per l'ordinamento cronologico."""
    try:
        match = re.search(r'📅 (\d{2}/\d{2}/\d{4} \d{2}:\d{2})', messaggio)
        if match:
            data_str = match.group(1)
            return datetime.strptime(data_str, '%d/%m/%Y %H:%M')
    except:
        pass
    return None

def controlla_feed(feed_info, fingerprints_visti):
    """Controlla un singolo feed per nuovi contenuti con sistema anti-duplicati migliorato per Instagram."""
    nuovi_contenuti = []
    try:
        feed_type = feed_info.get('type', 'rss')
        log_message(f"🔍 Controllo {feed_type}: {feed_info['name']}")
        log_message(f"📊 Fingerprints già visti: {len(fingerprints_visti)}")
        
        # Trova URL funzionante
        feed_url = trova_url_funzionante(feed_info)
        
        # Richiedi il feed
        response = requests.get(feed_url, headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            log_message(f"📭 Nessun contenuto in {feed_info['name']}")
            return nuovi_contenuti
        
        # Filtro temporale - per Instagram più permissivo (3 giorni)
        giorni_filtro = 3 if 'instagram' in feed_type else 2
        filtro_temporale = datetime.now() - timedelta(days=giorni_filtro)
        
        # Primo avvio - limiti diversi per tipo
        primo_avvio = len(fingerprints_visti) <= 1
        limite_primo_avvio = 2 if 'instagram' in feed_type else 1
        
        log_message(f"🎯 DEBUG: Primo avvio? {primo_avvio}, Limite: {limite_primo_avvio}")
        contenuti_processati = 0
        
        # Ordina per data
        entries_sorted = sorted(feed.entries, 
                              key=lambda x: getattr(x, 'published_parsed', (1970, 1, 1, 0, 0, 0, 0, 0, 0)), 
                              reverse=True)
        
        for entry in entries_sorted:
            if primo_avvio and contenuti_processati >= limite_primo_avvio:
                log_message(f"🛑 Primo avvio: limitato a {limite_primo_avvio} elementi per {feed_info['name']}")
                break
                
            link = getattr(entry, 'link', '').strip()
            titolo = getattr(entry, 'title', 'Titolo non disponibile').strip()
            
            if not link:
                continue
            
            # GENERA FINGERPRINT SPECIFICO PER TIPO
            fingerprint = genera_fingerprint_instagram(titolo, link, feed_type)
            log_message(f"🔗 Controllo: {titolo[:50]}... | FP: {fingerprint}")
            
            # Controllo duplicati più rigoroso per Instagram
            if fingerprint in fingerprints_visti:
                log_message(f"⏭ DEBUG: SKIP duplicato - {fingerprint}")
                
                # Per Instagram, controllo aggiuntivo con titolo simile
                if 'instagram' in feed_type:
                    titolo_norm = normalizza_titolo_instagram(titolo)
                    duplicato_trovato = False
                    for fp_esistente in fingerprints_visti:
                        if fp_esistente.startswith('ig_') and len(titolo_norm) > 10:
                            # Controllo se titoli molto simili (possibili varianti)
                            # Questo è un controllo aggiuntivo opzionale
                            pass
                    
                continue
            else:
                log_message(f"✅ DEBUG: NUOVO - {fingerprint}")
            
            # Controllo data
            pub_date = getattr(entry, 'published_parsed', None)
            if pub_date:
                entry_date = datetime(*pub_date[:6])
                if entry_date < filtro_temporale:
                    log_message(f"⏭ Skip contenuto vecchio: {entry_date.strftime('%d/%m/%Y %H:%M')}")
                    continue
                log_message(f"📅 Contenuto del: {entry_date.strftime('%d/%m/%Y %H:%M')}")
            elif primo_avvio:
                log_message(f"⏭ Skip contenuto senza data (primo avvio)")
                continue
            
            # Pulisci contenuto
            if 'instagram' in feed_type:
                titolo = pulisci_contenuto_instagram(titolo, link)
            
            # Crea messaggio
            messaggio = (
                f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                f"📰 {titolo}\n\n"
                f"🔗 {link}"
            )
            
            if pub_date:
                data_pub = datetime(*pub_date[:6]).strftime("%d/%m/%Y %H:%M")
                messaggio += f"\n📅 {data_pub}"
            
            if TEST_MODE:
                messaggio += f"\n🔍 FP: {fingerprint}"
                messaggio += f"\n📝 Tipo: {feed_type}"
            
            nuovi_contenuti.append({'fingerprint': fingerprint, 'messaggio': messaggio})
            fingerprints_visti.add(fingerprint)
            contenuti_processati += 1
            
            log_message(f"✅ DEBUG: NUOVO contenuto aggiunto - {fingerprint}")
        
        log_message(f"🆕 {len(nuovi_contenuti)} nuovi contenuti in {feed_info['name']}")
        
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Errore di rete per {feed_info['name']}: {e}", "ERROR")
        if 'instagram' in feed_info.get('type', ''):
            invia_messaggio_telegram(
                f"⚠ <b>{feed_info['name']}</b>\n\n"
                f"❌ Feed Instagram non disponibile\n"
                f"💡 Considera di usare RSS.app o Feedity\n"
                f"🔗 https://rss.app/rss-feed/create-instagram-rss-feed"
            )
    except Exception as e:
        log_message(f"❌ Errore generico nel feed {feed_info['name']}: {e}", "ERROR")
    
    return nuovi_contenuti

def invia_report_stato():
    """Invia un report dello stato del monitoraggio."""
    if TEST_MODE:
        return
        
    feeds_attivi = len(FEEDS_DA_MONITORARE)
    feeds_instagram = len([f for f in FEEDS_DA_MONITORARE if 'instagram' in f.get('type', '')])
    
    report = (
        f"📊 <b>RSS Monitor - Report Stato</b>\n\n"
        f"✅ Monitor attivo (v2.1 Instagram Fix)\n"
        f"📡 {feeds_attivi} feed monitorati\n"
        f"📸 {feeds_instagram} feed Instagram (anti-duplicati migliorato)\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"🛡 Sistema anti-duplicati specifico per Instagram\n"
        f"🎯 Fingerprint basati su ID post quando disponibili\n"
        f"⏰ Invio in ordine cronologico\n"
        f"🔧 Filtro temporale: 3 giorni per Instagram, 2 per altri"
    )
    
    invia_messaggio_telegram(report)

def main():
    log_message("=" * 60)
    log_message("🤖 RSS FEED MONITOR v2.1 - Instagram Fix Anti-Duplicati")
    log_message("=" * 60)
    log_message(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log_message(f"📋 Monitoraggio {len(FEEDS_DA_MONITORARE)} feed")
    log_message("-" * 60)
    
    if not verifica_configurazione():
        sys.exit(1)
    
    if TEST_MODE:
        log_message("🧪 Modalità test attivata")
        invia_messaggio_telegram("🧪 Test RSS Monitor v2.1 (Instagram Fix) completato con successo ✅")
        invia_report_stato()
        return
    
    fingerprints_visti = carica_link_visti()
    
    # Report stato periodico
    ora_corrente = datetime.now().hour
    if ora_corrente == 9:
        invia_report_stato()
    
    # FASE 1: Raccolta contenuti
    log_message("🔄 FASE 1: Raccolta contenuti da tutti i feed...")
    tutti_i_contenuti = []
    
    for feed_info in FEEDS_DA_MONITORARE:
        nuovi_contenuti = controlla_feed(feed_info, fingerprints_visti)
        for contenuto in nuovi_contenuti:
            tutti_i_contenuti.append({
                'messaggio': contenuto['messaggio'],
                'fingerprint': contenuto['fingerprint'],
                'feed_name': feed_info['name'],
                'feed_type': feed_info.get('type', 'rss'),
                'data_pub': estrai_data_da_messaggio(contenuto['messaggio'])
            })
    
    log_message(f"📦 Raccolti {len(tutti_i_contenuti)} nuovi contenuti totali")
    
    if not tutti_i_contenuti:
        log_message("📭 Nessun nuovo contenuto trovato")
        salva_link_visti(fingerprints_visti)
        log_message("=" * 60)
        return
    
    # FASE 2: Ordinamento cronologico
    log_message("🗂 FASE 2: Ordinamento cronologico...")
    
    def ordina_per_data(contenuto):
        data = contenuto['data_pub']
        if data:
            return data
        else:
            return datetime(1970, 1, 1)
    
    tutti_i_contenuti.sort(key=ordina_per_data)
    
    # Log ordine
    log_message("📋 Ordine di invio (dal più vecchio al più recente):")
    for i, contenuto in enumerate(tutti_i_contenuti, 1):
        data_str = contenuto['data_pub'].strftime('%d/%m %H:%M') if contenuto['data_pub'] else 'Senza data'
        tipo_str = f"[{contenuto['feed_type']}]" if contenuto['feed_type'] != 'rss' else ""
        log_message(f"   {i}. [{data_str}] {contenuto['feed_name']} {tipo_str}")
    
    # FASE 3: Invio messaggi
    log_message("📤 FASE 3: Invio messaggi in ordine cronologico...")
    nuovi_contenuti_totali = 0
    instagram_inviati = 0
    
    for contenuto in tutti_i_contenuti:
        if invia_messaggio_telegram(contenuto['messaggio']):
            nuovi_contenuti_totali += 1
            if 'instagram' in contenuto['feed_type']:
                instagram_inviati += 1
            log_message(f"✅ Inviato: {contenuto['feed_name']} | FP: {contenuto['fingerprint']}")
            
            # Pausa più lunga per Instagram per evitare problemi
            if 'instagram' in contenuto['feed_type']:
                time.sleep(3)
            else:
                time.sleep(2)
        else:
            log_message(f"❌ Errore invio: {contenuto['feed_name']}")
    
    # Salva stato finale
    salva_link_visti(fingerprints_visti)
    
    # Report finale
    log_message("=" * 60)
    log_message(f"📤 {nuovi_contenuti_totali} contenuti inviati ({instagram_inviati} Instagram)")
    log_message(f"💾 {len(fingerprints_visti)} fingerprints tracciati")
    
    # Conta fingerprints Instagram
    instagram_fps = len([fp for fp in fingerprints_visti if fp.startswith('ig_')])
    log_message(f"📸 {instagram_fps} fingerprints Instagram specifici")
    log_message("🎯 Sistema anti-duplicati Instagram attivo")
    log_message("=" * 60)

if _name_ == "_main_":
    try:
        main()
    except KeyboardInterrupt:
        log_message("⏹ Interruzione manuale")
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 Errore critico: {e}", "ERROR")
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            invia_messaggio_telegram(f"🚨 <b>RSS Monitor v2.1 - Errore Critico</b>\n\n❌ {str(e)}")
        sys.exit(1)
