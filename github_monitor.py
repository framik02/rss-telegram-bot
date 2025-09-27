

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Feed Monitor per GitHub Actions
Versione ottimizzata con fix per Instagram
"""

import requests
import feedparser
import json
import os
import sys
import time
from datetime import datetime, timedelta
import re

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
        "url": "https://rss.app/feeds/eSz39hnyubmwLjuW.xml",  # Sostituisci con URL RSS.app
        "type": "instagram_alt",
        "backup_urls": [
            "https://rsshub.ktachibana.party/instagram/user/fratelliditalia",
            "https://rss.shab.fun/instagram/user/fratelliditalia"
        ]
    },
    {
        "name": "Instagram - Ministero del Lavoro",
        "emoji": "🚀",
        "url": "https://rss.app/feeds/O2NQW8pvSIQGpkby.xml",  # Sostituisci con URL RSS.app
        "type": "instagram_alt",
        "backup_urls": [
            "https://rsshub.ktachibana.party/instagram/user/minlavoro",
            "https://rss.shab.fun/instagram/user/minlavoro"
        ]
    },
    {
        "name": "Instagram - Meloni",
        "emoji": "📸", 
        "url": "https://rss.app/feeds/opRYqgialL3uzDej.xml",  # Sostituisci con URL RSS.app
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
    """Carica i link già visti dal file JSON locale o da GitHub Gist."""
    # Prima prova a caricare da GitHub Gist (persistente)
    link_da_gist = carica_da_gist()
    if link_da_gist:
        return link_da_gist
    
    # Se non c'è Gist, prova il file locale
    if not os.path.exists(FILE_VISTI):
        log_message(f"📁 File {FILE_VISTI} non trovato - primo avvio")
        
        # PRIMO AVVIO: crea un set iniziale con timestamp per evitare spam
        primo_avvio_marker = f"primo_avvio_{datetime.now().strftime('%Y%m%d')}"
        log_message(f"🎯 Primo avvio rilevato - modalità inizializzazione attiva")
        return {primo_avvio_marker}
    
    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return set()
            data = json.loads(content)
            links = set(data.get('link_visti', []))
            
            # Controlla età dei dati
            ultimo_aggiornamento = data.get('ultimo_aggiornamento', '')
            if ultimo_aggiornamento:
                try:
                    ultima_data = datetime.fromisoformat(ultimo_aggiornamento.replace('Z', '+00:00'))
                    giorni_fa = (datetime.now() - ultima_data.replace(tzinfo=None)).days
                    if giorni_fa > 7:
                        log_message(f"⚠️ Dati vecchi di {giorni_fa} giorni - reset parziale")
                        # Mantieni solo link recenti (simulazione)
                        return set(list(links)[-100:]) if len(links) > 100 else links
                except:
                    pass
            
            log_message(f"📂 Caricati {len(links)} link già processati")
            return links
    except Exception as e:
        log_message(f"❌ Errore nel leggere {FILE_VISTI}: {e}", "ERROR")
        return set()

def salva_link_visti(link_visti):
    """Salva i link visti nel file JSON locale con gestione GitHub Gist."""
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_link': len(link_visti),
            'link_visti': sorted(list(link_visti)),
            'github_action': True,
            'repository': os.getenv('GITHUB_REPOSITORY', 'unknown'),
            'run_id': os.getenv('GITHUB_RUN_ID', 'unknown')
        }
        
        # Salva localmente
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log_message(f"💾 Salvati {len(link_visti)} link nel file {FILE_VISTI}")
        
        # Prova a sincronizzare con GitHub Gist per persistenza
        salva_su_gist(data)
        
        return True
    except Exception as e:
        log_message(f"❌ Errore nel salvare {FILE_VISTI}: {e}", "ERROR")
        return False

def salva_su_gist(data):
    """Salva i dati su GitHub Gist per persistenza tra le esecuzioni."""
    if not GITHUB_TOKEN:
        return
        
    gist_id = os.getenv('GIST_ID', '')  # Aggiungi questo come secret
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
            log_message("☁️ Dati sincronizzati con GitHub Gist")
        else:
            log_message(f"⚠️ Errore sync Gist: {response.status_code}")
            
    except Exception as e:
        log_message(f"⚠️ Errore sincronizzazione Gist: {e}")

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
                links = set(data.get('link_visti', []))
                log_message(f"☁️ Caricati {len(links)} link da GitHub Gist")
                return links
                
    except Exception as e:
        log_message(f"⚠️ Errore caricamento da Gist: {e}")
        
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
    
    log_message(f"⚠️ Nessun URL funzionante per {feed_info['name']}")
    return feed_info['url']  # Ritorna l'originale come fallback

def prova_rsshub_instances(url_originale):
    """Prova diverse istanze RSSHub se quella principale non funziona."""
    for instance in RSSHUB_INSTANCES:
        try:
            # Estrai il path dall'URL originale
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
    
    log_message("⚠️ Nessuna istanza RSSHub disponibile")
    return url_originale

def pulisci_contenuto_instagram(titolo, link):
    """Pulisce e migliora il contenuto Instagram."""
    # Rimuovi caratteri speciali dal titolo
    titolo_pulito = re.sub(r'[^\w\s\-_.,!?]', '', titolo)
    
    # Accorcia titoli troppo lunghi
    if len(titolo_pulito) > 100:
        titolo_pulito = titolo_pulito[:97] + "..."
    
    return titolo_pulito

def controlla_feed(feed_info, link_visti):
    """Controlla un singolo feed per nuovi contenuti."""
    nuovi_contenuti = []
    try:
        log_message(f"🔍 Controllo {feed_info.get('type', 'rss')}: {feed_info['name']}")
        
        # Trova URL funzionante
        feed_url = trova_url_funzionante(feed_info)
        
        # Richiedi il feed con headers appropriati
        response = requests.get(feed_url, headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            log_message(f"📭 Nessun contenuto in {feed_info['name']}")
            return nuovi_contenuti
        
        # FILTRO TEMPORALE RIGOROSO - Solo ultimi 2 giorni per sicurezza
        due_giorni_fa = datetime.now() - timedelta(days=2)
        
        # Primo avvio: prendi solo ultimo elemento per feed per evitare spam
        primo_avvio = len(link_visti) == 0
        contenuti_processati = 0
        
        # Ordina per data (più recenti prima)
        entries_sorted = sorted(feed.entries, 
                              key=lambda x: getattr(x, 'published_parsed', (1970, 1, 1, 0, 0, 0, 0, 0, 0)), 
                              reverse=True)
        
        for entry in entries_sorted:
            # Limite per primo avvio: massimo 1 elemento per feed
            if primo_avvio and contenuti_processati >= 1:
                log_message(f"🛑 Primo avvio: limitato a 1 elemento per {feed_info['name']}")
                break
                
            link = getattr(entry, 'link', '').strip()
            titolo = getattr(entry, 'title', 'Titolo non disponibile').strip()
            
            if not link or link in link_visti:
                continue
            
            # CONTROLLO DATA RIGOROSO
            pub_date = getattr(entry, 'published_parsed', None)
            if pub_date:
                entry_date = datetime(*pub_date[:6])
                
                # Skip contenuti vecchi
                if entry_date < due_giorni_fa:
                    log_message(f"⏭️ Skip contenuto vecchio: {entry_date.strftime('%d/%m/%Y %H:%M')}")
                    continue
                    
                # Log della data per debug
                log_message(f"📅 Contenuto del: {entry_date.strftime('%d/%m/%Y %H:%M')}")
            else:
                # Se non ha data, è probabilmente vecchio - skip in caso di primo avvio
                if primo_avvio:
                    log_message(f"⏭️ Skip contenuto senza data (primo avvio)")
                    continue
            
            # Pulisci contenuto Instagram
            tipo = feed_info.get('type', 'rss')
            if 'instagram' in tipo:
                titolo = pulisci_contenuto_instagram(titolo, link)
            
            # Crea messaggio
            messaggio = (
                f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                f"📰 {titolo}\n\n"
                f"🔗 {link}"
            )
            
            # Aggiungi info sulla data se disponibile
            if pub_date:
                data_pub = datetime(*pub_date[:6]).strftime("%d/%m/%Y %H:%M")
                messaggio += f"\n📅 {data_pub}"
            
            nuovi_contenuti.append({'link': link, 'messaggio': messaggio})
            link_visti.add(link)
            contenuti_processati += 1
        
        if primo_avvio and contenuti_processati > 0:
            log_message(f"🎯 Primo avvio: {contenuti_processati} contenuto inizializzato per {feed_info['name']}")
        else:
            log_message(f"🆕 {len(nuovi_contenuti)} nuovi contenuti in {feed_info['name']}")
        
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Errore di rete per {feed_info['name']}: {e}", "ERROR")
        # Per Instagram, suggerisci soluzioni alternative
        if 'instagram' in feed_info.get('type', ''):
            invia_messaggio_telegram(
                f"⚠️ <b>{feed_info['name']}</b>\n\n"
                f"❌ Feed Instagram non disponibile\n"
                f"💡 Considera di usare RSS.app o Feedity per questo account\n"
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
        f"✅ Monitor attivo\n"
        f"📡 {feeds_attivi} feed monitorati\n"
        f"📸 {feeds_instagram} feed Instagram\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"ℹ️ I feed Instagram potrebbero richiedere configurazione aggiuntiva"
    )
    
    invia_messaggio_telegram(report)

def main():
    log_message("=" * 60)
    log_message("🤖 RSS FEED MONITOR - GitHub Actions (Instagram Fixed)")
    log_message("=" * 60)
    log_message(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log_message(f"📋 Monitoraggio {len(FEEDS_DA_MONITORARE)} feed")
    log_message("-" * 60)
    
    if not verifica_configurazione():
        sys.exit(1)
    
    if TEST_MODE:
        log_message("🧪 Modalità test attivata")
        invia_messaggio_telegram("🧪 Test RSS Monitor (Instagram Fixed) completato con successo ✅")
        invia_report_stato()
        return
    
    link_visti = carica_link_visti()
    nuovi_contenuti_totali = 0
    
    # Invia report di stato ogni tanto (es. una volta al giorno)
    ora_corrente = datetime.now().hour
    if ora_corrente == 9:  # Alle 9:00
        invia_report_stato()
    
    for feed_info in FEEDS_DA_MONITORARE:
        nuovi_contenuti = controlla_feed(feed_info, link_visti)
        for contenuto in nuovi_contenuti:
            if invia_messaggio_telegram(contenuto['messaggio']):
                nuovi_contenuti_totali += 1
                time.sleep(2)  # Pausa più lunga per evitare rate limiting
    
    salva_link_visti(link_visti)
    
    log_message("=" * 60)
    log_message(f"📤 {nuovi_contenuti_totali} nuovi contenuti inviati")
    log_message(f"💾 {len(link_visti)} link tracciati")
    
    # Messaggio finale se non ci sono nuovi contenuti
    if nuovi_contenuti_totali == 0:
        log_message("📭 Nessun nuovo contenuto trovato")
    
    log_message("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("⏹️ Interruzione manuale")
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 Errore critico: {e}", "ERROR")
        # Invia notifica di errore critico
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            invia_messaggio_telegram(f"🚨 <b>RSS Monitor - Errore Critico</b>\n\n❌ {str(e)}")
        sys.exit(1)
