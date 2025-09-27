#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Feed Monitor per GitHub Actions
Versione ottimizzata per girare su GitHub Actions con gestione errori avanzata
"""

import requests
import feedparser
import json
import os
import sys
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
    # I tuoi Google Alerts esistenti
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
    
    # Instagram tramite RSSHub (GRATUITO)
    {
        "name": "Instagram - fdi",
        "emoji": "📸",
        "url": "https://www.instagram.com/fratelliditalia",
        "type": "instagram"
    },
    {
        "name": "Instagram - mlps", 
        "emoji": "🚀",
        "url": "https://www.instagram.com/minlavoro",
        "type": "instagram"
    },
    
    # Esempi di altri servizi (decommentali se vuoi usarli)
    # {
    #     "name": "Twitter - Elon Musk",
    #     "emoji": "🐦",
    #     "url": "https://rsshub.app/twitter/user/elonmusk",
    #     "type": "twitter"
    # },
    # {
    #     "name": "YouTube - Veritasium", 
    #     "emoji": "📺",
    #     "url": "https://rsshub.app/youtube/user/@veritasium",
    #     "type": "youtube"
    # },
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
        
        log_message("\n🔧 COME RISOLVERE:", "INFO")
        log_message("1. Vai su Settings > Secrets and variables > Actions", "INFO")
        log_message("2. Aggiungi Repository Secrets:", "INFO")
        log_message("   - TELEGRAM_TOKEN: token del tuo bot", "INFO")
        log_message("   - TELEGRAM_CHAT_ID: il tuo chat ID", "INFO")
        log_message("\n📖 Guida completa: README.md", "INFO")
        
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
                log_message("📄 File stato vuoto")
                return set()
            
            data = json.loads(content)
            links = set(data.get('link_visti', []))
            
            log_message(f"📂 Caricati {len(links)} link già processati")
            return links
            
    except json.JSONDecodeError as e:
        log_message(f"❌ Errore JSON nel file {FILE_VISTI}: {e}", "ERROR")
        return set()
    except Exception as e:
        log_message(f"❌ Errore nel leggere {FILE_VISTI}: {e}", "ERROR")
        return set()

def salva_link_visti(link_visti):
    """Salva i link visti nel file JSON locale."""
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_link': len(link_visti),
            'link_visti': sorted(list(link_visti)),  # Ordina per consistenza
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
        
    except requests.exceptions.Timeout:
        log_message("⏱️ Timeout nell'invio Telegram", "ERROR")
        return False
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
        
        # Se è RSSHub, prova il failover se necessario
        if "rsshub.app" in feed_url:
            try:
                test_response = requests.head(feed_url, timeout=10)
                if test_response.status_code != 200:
                    log_message("⚠️ Istanza RSSHub principale non risponde, provo alternative")
                    feed_url = prova_rsshub_instances(feed_url)
            except:
                feed_url = prova_rsshub_instances(feed_url)
        
        # Parsing del feed con timeout
        try:
            response = requests.get(feed_url, timeout=15)
            feed = feedparser.parse(response.content)
        except requests.exceptions.Timeout:
            log_message(f"⏱️ Timeout nel download feed {feed_info['name']}")
            return nuovi_contenuti
        except Exception as e:
            log_message(f"❌ Errore download feed {feed_info['name']}: {e}")
            return nuovi_contenuti
        
        if feed.bozo:
            log_message(f"⚠️ Feed potenzialmente malformato: {feed_info['name']}")
        
        if not feed.entries:
            log_message(f"📭 Nessun contenuto trovato in {feed_info['name']}")
            return nuovi_contenuti
        
        # Controlla ogni entry
        for entry in feed.entries:
            link = getattr(entry, 'link', '').strip()
            
            if not link or link in link_visti:
                continue
            
            titolo = getattr(entry, 'title', 'Titolo non disponibile').strip()
            
            # Formatting per tipo di contenuto
            tipo = feed_info.get('type', 'rss')
            
            if tipo == 'instagram':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"📸 Nuovo post Instagram\n"
                    f"📝 {titolo[:100]}{'...' if len(titolo) > 100 else ''}\n\n"
                    f"🔗 {link}"
                )
            elif tipo == 'twitter':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"🐦 Nuovo tweet\n"
                    f"💬 {titolo[:150]}{'...' if len(titolo) > 150 else ''}\n\n"
                    f"🔗 {link}"
                )
            elif tipo == 'youtube':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"📺 Nuovo video\n"
                    f"🎬 {titolo}\n\n"
                    f"🔗 {link}"
                )
            else:  # RSS tradizionale
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"📰 {titolo}\n\n"
                    f"🔗 {link}"
                )
            
            nuovi_contenuti.append({
                'link': link,
                'messaggio': messaggio,
                'feed_name': feed_info['name']
            })
            
            link_visti.add(link)
        
        if nuovi_contenuti:
            log_message(f"🆕 Trovati {len(nuovi_contenuti)} nuovi contenuti in {feed_info['name']}")
        else:
            log_message(f"📭 Nessun contenuto nuovo in {feed_info['name']}")
            
    except Exception as e:
        log_message(f"❌ Errore generico nel controllare {feed_info['name']}: {e}", "ERROR")
    
    return nuovi_contenuti

def invia_messaggio_test():
    """Invia un messaggio di test."""
    messaggio = (
        "🧪 <b>TEST RSS FEED MONITOR</b>\n\n"
        f"✅ GitHub Actions funzionante\n"
        f"⏰ Test eseguito: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"🏗️ Repository: {os.getenv('GITHUB_REPOSITORY', 'unknown')}\n"
        f"🔄 Run ID: {os.getenv('GITHUB_RUN_ID', 'unknown')}\n\n"
        "🚀 Monitor attivo e pronto!"
    )
    
    return invia_messaggio_telegram(messaggio)

def main():
    """Funzione principale per GitHub Actions."""
    log_message("=" * 60)
    log_message("🤖 RSS FEED MONITOR - GitHub Actions")
    log_message("=" * 60)
    log_message(f"📅 Esecuzione: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log_message(f"📋 Monitoraggio {len(FEEDS_DA_MONITORARE)} feed")
    log_message(f"🏗️ Repository: {os.getenv('GITHUB_REPOSITORY', 'unknown')}")
    log_message(f"🔄 Run ID: {os.getenv('GITHUB_RUN_ID', 'unknown')}")
    log_message("-" * 60)
    
    # Verifica configurazione
    if not verifica_configurazione():
        sys.exit(1)
    
    # Modalità test
    if TEST_MODE:
        log_message("🧪 MODALITÀ TEST ATTIVATA")
        if invia_messaggio_test():
            log_message("✅ Test completato con successo")
        else:
            log_message("❌ Test fallito", "ERROR")
            sys.exit(1)
        return
    
    # Carica stato precedente
    link_visti = carica_link_visti()
    
    # Controlla tutti i feed
    nuovi_contenuti_totali = 0
    feed_errori = 0
    
    for feed_info in FEEDS_DA_MONITORARE:
        try:
            nuovi_contenuti = controlla_feed(feed_info, link_visti)
            
            # Invia ogni nuovo contenuto
            for contenuto in nuovi_contenuti:
                if invia_messaggio_telegram(contenuto['messaggio']):
                    nuovi_contenuti_totali += 1
                    # Piccola pausa per evitare rate limiting
                    import time
                    time.sleep(1)
                else:
                    # Se l'invio fallisce, rimuovi dai visti per ritentare
                    link_visti.discard(contenuto['link'])
                    
        except Exception as e:
            log_message(f"❌ Errore grave nel processare feed {feed_info.get('name', 'unknown')}: {e}", "ERROR")
            feed_errori += 1
    
    # Salva stato aggiornato
    if not salva_link_visti(link_visti):
        log_message("⚠️ Impossibile salvare stato", "WARNING")
    
    # Riepilogo finale
    log_message("\n" + "=" * 60)
    log_message(f"📤 RIEPILOGO: {nuovi_contenuti_totali} nuovi contenuti inviati")
    if feed_errori > 0:
        log_message(f"⚠️ {feed_errori} feed con errori")
    log_message(f"💾 Stato salvato: {len(link_visti)} link totali tracciati")
    log_message(f"⏰ Prossima esecuzione: ~10 minuti")
    log_message("=" * 60)
    
    if nuovi_contenuti_totali == 0 and feed_errori == 0:
        log_message("😴 Nessun nuovo contenuto trovato in questo ciclo")
    
    # Exit code basato sui risultati
    if feed_errori > len(FEEDS_DA_MONITORARE) // 2:  # Più della metà dei feed ha errori
        log_message("❌ Troppi feed con errori", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("⏹️ Interruzione manuale")
        sys.exit(0)
    except Exception as e:
        log_message(f"💥 Errore critico: {e}", "ERROR")
        sys.exit(1)"type": "instagram"
    },
    {
        "name": "Instagram - National Geographic",
        "emoji": "📸",
        "url": "https://rsshub.app/instagram/user/natgeo",
        "type": "instagram"
    },
    
    # Esempi di altri servizi (decommentali se vuoi usarli)
    # {
    #     "name": "Twitter - Elon Musk",
    #     "emoji": "🐦",
    #     "url": "https://rsshub.app/twitter/user/elonmusk",
    #     "type": "twitter"
    # },
    # {
    #     "name": "YouTube - Veritasium", 
    #     "emoji": "📺",
    #     "url": "https://rsshub.app/youtube/user/@veritasium",
    #     "type": "youtube"
    # },
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

def carica_link_visti():
    """Carica i link già visti dal file JSON locale."""
    if not os.path.exists(FILE_VISTI):
        print(f"📁 File {FILE_VISTI} non trovato")
        return set()
    
    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            data = json.load(f)
            links = set(data.get('link_visti', []))
            print(f"📂 Caricati {len(links)} link già processati")
            return links
    except Exception as e:
        print(f"❌ Errore nel leggere {FILE_VISTI}: {e}")
        return set()

def salva_link_visti(link_visti):
    """Salva i link visti nel file JSON locale."""
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_link': len(link_visti),
            'link_visti': list(link_visti),
            'github_action': True,
            'repository': os.getenv('GITHUB_REPOSITORY', 'unknown')
        }
        
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Salvati {len(link_visti)} link nel file {FILE_VISTI}")
        return True
    except Exception as e:
        print(f"❌ Errore nel salvare {FILE_VISTI}: {e}")
        return False

def invia_messaggio_telegram(messaggio):
    """Invia un messaggio su Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Token Telegram non configurato")
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
        print(f"✅ Messaggio inviato su Telegram")
        return True
    except Exception as e:
        print(f"❌ Errore nell'invio Telegram: {e}")
        return False

def prova_rsshub_instances(url_originale):
    """Prova diverse istanze RSSHub se quella principale non funziona."""
    for instance in RSSHUB_INSTANCES:
        try:
            if url_originale.startswith("https://rsshub.app"):
                test_url = url_originale.replace("https://rsshub.app", instance)
                
                response = requests.head(test_url, timeout=10)
                if response.status_code == 200:
                    return test_url
                    
        except:
            continue
    
    return url_originale

def controlla_feed(feed_info, link_visti):
    """Controlla un singolo feed per nuovi contenuti."""
    nuovi_contenuti = []
    
    try:
        print(f"🔍 Controllo {feed_info.get('type', 'rss')}: {feed_info['name']}")
        
        feed_url = feed_info['url']
        
        # Se è RSSHub, prova il failover se necessario
        if "rsshub.app" in feed_url:
            try:
                test_response = requests.head(feed_url, timeout=10)
                if test_response.status_code != 200:
                    feed_url = prova_rsshub_instances(feed_url)
            except:
                feed_url = prova_rsshub_instances(feed_url)
        
        # Parsing del feed
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            print(f"⚠️  Feed potenzialmente malformato: {feed_info['name']}")
        
        # Controlla ogni entry
        for entry in feed.entries:
            link = getattr(entry, 'link', '')
            
            if not link or link in link_visti:
                continue
            
            titolo = getattr(entry, 'title', 'Titolo non disponibile')
            
            # Formatting per tipo di contenuto
            tipo = feed_info.get('type', 'rss')
            
            if tipo == 'instagram':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"📸 Nuovo post Instagram\n"
                    f"📝 {titolo[:100]}{'...' if len(titolo) > 100 else ''}\n\n"
                    f"🔗 {link}"
                )
            elif tipo == 'twitter':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"🐦 Nuovo tweet\n"
                    f"💬 {titolo[:150]}{'...' if len(titolo) > 150 else ''}\n\n"
                    f"🔗 {link}"
                )
            elif tipo == 'youtube':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"📺 Nuovo video\n"
                    f"🎬 {titolo}\n\n"
                    f"🔗 {link}"
                )
            else:  # RSS tradizionale
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"📰 {titolo}\n\n"
                    f"🔗 {link}"
                )
            
            nuovi_contenuti.append({
                'link': link,
                'messaggio': messaggio,
                'feed_name': feed_info['name']
            })
            
            link_visti.add(link)
        
        if nuovi_contenuti:
            print(f"🆕 Trovati {len(nuovi_contenuti)} nuovi contenuti in {feed_info['name']}")
        else:
            print(f"📭 Nessun contenuto nuovo in {feed_info['name']}")
            
    except Exception as e:
        print(f"❌ Errore nel controllare {feed_info['name']}: {e}")
    
    return nuovi_contenuti

def main():
    """Funzione principale per GitHub Actions."""
    print("=" * 60)
    print("🤖 RSS FEED MONITOR - GitHub Actions")
    print("=" * 60)
    print(f"📅 Esecuzione: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📋 Monitoraggio {len(FEEDS_DA_MONITORARE)} feed")
    print(f"🏗️  Repository: {os.getenv('GITHUB_REPOSITORY', 'unknown')}")
    print("-" * 60)
    
    # Verifica configurazione
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERRORE: Secrets Telegram non configurati!")
        print("\n🔧 SETUP RICHIESTO:")
        print("1. Vai su Settings > Secrets and variables > Actions")
        print("2. Aggiungi questi Repository Secrets:")
        print("   - TELEGRAM_TOKEN: il token del tuo bot")
        print("   - TELEGRAM_CHAT_ID: il tuo chat ID")
        print("\n📖 Guida completa nel README.md")
        return
    
    # Carica stato precedente
    link_visti = carica_link_visti()
    
    # Controlla tutti i feed
    nuovi_contenuti_totali = 0
    
    for feed_info in FEEDS_DA_MONITORARE:
        nuovi_contenuti = controlla_feed(feed_info, link_visti)
        
        # Invia ogni nuovo contenuto
        for contenuto in nuovi_contenuti:
            if invia_messaggio_telegram(contenuto['messaggio']):
                nuovi_contenuti_totali += 1
                # Piccola pausa per evitare rate limiting
                import time
                time.sleep(1)
            else:
                # Se l'invio fallisce, rimuovi dai visti per ritentare
                link_visti.discard(contenuto['link'])
    
    # Salva stato aggiornato
    salva_link_visti(link_visti)
    
    # Riepilogo
    print("\n" + "=" * 60)
    print(f"📤 RIEPILOGO: {nuovi_contenuti_totali} nuovi contenuti inviati")
    print(f"💾 Stato salvato: {len(link_visti)} link totali tracciati")
    print(f"⏰ Prossima esecuzione: tra 10 minuti (automatica)")
    print("=" * 60)
    
    if nuovi_contenuti_totali == 0:
        print("😴 Nessun nuovo contenuto trovato in questo ciclo")

if __name__ == "__main__":
    main()
    
    
    
    

