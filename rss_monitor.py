
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS Feed Monitor con Instagram e notifiche Telegram
Monitora feed RSS e post Instagram, invia notifiche su Telegram per nuovi contenuti

Supporta:
- Feed RSS tradizionali
- Post Instagram tramite RSSHub
- Account Twitter/X tramite RSSHub
- YouTube, Reddit e altri servizi

GitHub: https://github.com/tuousername/rss-telegram-monitor
"""

import requests
import feedparser
import time
import json
import os
from datetime import datetime

# ================================
# CONFIGURAZIONE
# ================================

# Token del bot Telegram (ottienilo da @BotFather)
# IMPORTANTE: Per GitHub, usa variabili d'ambiente o file config.json
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Chat ID dove inviare i messaggi
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# File per salvare i link già inviati
FILE_VISTI = "visti.json"

# Tempo di attesa tra i controlli (in secondi) - 600 = 10 minuti
INTERVALLO_CONTROLLO = int(os.getenv("INTERVALLO_CONTROLLO", "600"))

# Lista dei feed da monitorare
# Supporta RSS tradizionali e servizi tramite RSSHub
FEEDS_DA_MONITORARE = [
    # Google Alerts (i tuoi feed esistenti)
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
    
    # Altri servizi social tramite RSSHub
    # {
    #     "name": "Twitter - @username",
    #     "emoji": "🐦",
    #     "url": "https://rsshub.app/twitter/user/username",
    #     "type": "twitter"
    # },
    # {
    #     "name": "YouTube - Channel",
    #     "emoji": "📺", 
    #     "url": "https://rsshub.app/youtube/user/@channelname",
    #     "type": "youtube"
    # },
    # {
    #     "name": "Reddit - Subreddit",
    #     "emoji": "🤖",
    #     "url": "https://rsshub.app/reddit/r/python",
    #     "type": "reddit"
    # }
]

# RSSHub instances (fallback se il principale non funziona)
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rss.shab.fun", 
    "https://rsshub.ktachibana.party",
    "https://rsshub.feeded.xyz"
]

# ================================
# FUNZIONI UTILITY
# ================================

def carica_configurazione():
    """
    Carica configurazione da file config.json se esiste.
    Utile per deployment senza esporre token.
    """
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"❌ Errore nel leggere {config_file}: {e}")
    
    return {
        "telegram_token": TELEGRAM_TOKEN,
        "telegram_chat_id": TELEGRAM_CHAT_ID,
        "intervallo_controllo": INTERVALLO_CONTROLLO
    }

def carica_link_visti():
    """
    Carica la lista dei link già inviati dal file JSON.
    Se il file non esiste, restituisce un set vuoto.
    """
    if not os.path.exists(FILE_VISTI):
        print(f"📁 File {FILE_VISTI} non trovato, ne creerò uno nuovo")
        return set()

    try:
        with open(FILE_VISTI, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('link_visti', []))
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Errore nel leggere {FILE_VISTI}: {e}")
        return set()

def salva_link_visti(link_visti):
    """
    Salva la lista dei link già inviati nel file JSON.
    """
    try:
        data = {
            'ultimo_aggiornamento': datetime.now().isoformat(),
            'totale_link': len(link_visti),
            'link_visti': list(link_visti)
        }
        with open(FILE_VISTI, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Salvati {len(link_visti)} link nel file {FILE_VISTI}")
    except Exception as e:
        print(f"❌ Errore nel salvare {FILE_VISTI}: {e}")

def invia_messaggio_telegram(messaggio, token, chat_id):
    """
    Invia un messaggio tramite l'API di Telegram.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': messaggio,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }

    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        print(f"✅ Messaggio inviato su Telegram")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nell'inviare messaggio Telegram: {e}")
        return False

def prova_rsshub_instances(url_path):
    """
    Prova diverse istanze RSSHub se quella principale non funziona.
    """
    for instance in RSSHUB_INSTANCES:
        try:
            # Sostituisce il dominio RSSHub nell'URL
            if url_path.startswith("https://rsshub.app"):
                test_url = url_path.replace("https://rsshub.app", instance)
            else:
                continue
                
            print(f"🔍 Provo istanza RSSHub: {instance}")
            response = requests.get(test_url, timeout=15)
            
            if response.status_code == 200:
                return test_url
                
        except requests.exceptions.RequestException:
            continue
    
    return url_path  # Ritorna l'URL originale se nessuna istanza funziona

def controlla_feed(feed_info, link_visti):
    """
    Controlla un singolo feed per nuovi contenuti.
    Supporta diversi tipi di contenuto tramite RSSHub.
    """
    nuovi_link = []

    try:
        print(f"🔍 Controllo {feed_info.get('type', 'rss')}: {feed_info['name']}")

        feed_url = feed_info['url']
        
        # Se è un feed RSSHub e fallisce, prova altre istanze
        if "rsshub.app" in feed_url:
            try:
                test_response = requests.get(feed_url, timeout=15)
                if test_response.status_code != 200:
                    feed_url = prova_rsshub_instances(feed_url)
            except:
                feed_url = prova_rsshub_instances(feed_url)

        # Scarica e parsa il feed
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            print(f"⚠️  Warning: feed malformato per {feed_info['name']}")

        # Controlla ogni entry nel feed
        for entry in feed.entries:
            link = getattr(entry, 'link', '')

            if not link or link in link_visti:
                continue

            titolo = getattr(entry, 'title', 'Titolo non disponibile')
            
            # Formatting specifico per tipo di contenuto
            tipo_contenuto = feed_info.get('type', 'rss')
            
            if tipo_contenuto == 'instagram':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"
                    f"📸 Nuovo post Instagram\n"
                    f"📝 {titolo}\n\n"
                    f"🔗 {link}"
                )
            elif tipo_contenuto == 'twitter':
                messaggio = (
                    f"{feed_info['emoji']} <b>{feed_info['name']}</b>\n\n"  
                    f"🐦 Nuovo tweet\n"
                    f"💬 {titolo}\n\n"
                    f"🔗 {link}"
                )
            elif tipo_contenuto == 'youtube':
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

            nuovi_link.append({
                'link': link,
                'messaggio': messaggio,
                'feed_name': feed_info['name']
            })

            link_visti.add(link)

        if nuovi_link:
            print(f"🆕 Trovati {len(nuovi_link)} nuovi contenuti in {feed_info['name']}")
        else:
            print(f"📭 Nessun nuovo contenuto in {feed_info['name']}")

    except Exception as e:
        print(f"❌ Errore nel controllare feed {feed_info['name']}: {e}")

    return nuovi_link

def stampa_info_progetto():
    """
    Stampa informazioni sul progetto per GitHub.
    """
    print("=" * 60)
    print("📡 RSS FEED MONITOR CON INSTAGRAM")
    print("=" * 60)
    print("🔹 Monitora feed RSS tradizionali")
    print("🔹 Monitora Instagram tramite RSSHub (GRATUITO)")
    print("🔹 Monitora Twitter, YouTube, Reddit e altri")
    print("🔹 Invia notifiche su Telegram")
    print("🔹 Open Source - GitHub: tuousername/rss-telegram-monitor")
    print("=" * 60)

def main():
    """
    Funzione principale che esegue il monitoraggio continuo.
    """
    stampa_info_progetto()
    
    # Carica configurazione
    config = carica_configurazione()
    token = config.get('telegram_token', '')
    chat_id = config.get('telegram_chat_id', '')
    intervallo = config.get('intervallo_controllo', 600)

    print(f"⏰ Controllo ogni {intervallo//60} minuti")
    print(f"📋 Monitoraggio {len(FEEDS_DA_MONITORARE)} feed")
    print("-" * 50)

    # Verifica configurazione
    if not token or not chat_id:
        print("❌ ERRORE: Token Telegram non configurato!")
        print("\n🔧 CONFIGURAZIONE:")
        print("1. Crea un file config.json con:")
        print('   {')
        print('     "telegram_token": "IL_TUO_TOKEN",')
        print('     "telegram_chat_id": "IL_TUO_CHAT_ID"') 
        print('   }')
        print("\n2. Oppure usa variabili d'ambiente:")
        print("   export TELEGRAM_TOKEN='il_tuo_token'")
        print("   export TELEGRAM_CHAT_ID='il_tuo_chat_id'")
        print("\n📖 Guida completa: README.md del repository")
        return

    # Carica link già visti
    link_visti = carica_link_visti()
    print(f"💾 Caricati {len(link_visti)} link già processati")

    # Loop principale
    ciclo = 0
    try:
        while True:
            ciclo += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n🔄 Ciclo #{ciclo} - {timestamp}")

            nuovi_contenuti_totali = 0

            # Controlla ogni feed
            for feed_info in FEEDS_DA_MONITORARE:
                nuovi_link = controlla_feed(feed_info, link_visti)

                # Invia ogni nuovo contenuto trovato
                for contenuto in nuovi_link:
                    if invia_messaggio_telegram(contenuto['messaggio'], token, chat_id):
                        nuovi_contenuti_totali += 1
                        # Pausa tra messaggi per evitare rate limiting
                        time.sleep(1)
                    else:
                        # Se l'invio fallisce, rimuovi il link per ritentare
                        link_visti.discard(contenuto['link'])

            # Salva i link visti
            if nuovi_contenuti_totali > 0:
                salva_link_visti(link_visti)
                print(f"📤 Inviati {nuovi_contenuti_totali} nuovi contenuti")
            else:
                print("😴 Nessun nuovo contenuto trovato")

            print(f"⏳ Prossimo controllo tra {intervallo//60} minuti...")
            time.sleep(intervallo)

    except KeyboardInterrupt:
        print("\n\n⏹️  Interruzione manuale rilevata")
        salva_link_visti(link_visti)
        print("💾 Link visti salvati")
        print("👋 RSS Feed Monitor terminato")

    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        salva_link_visti(link_visti)
        print("💾 Link visti salvati prima della chiusura")

# ================================
# AVVIO PROGRAMMA
# ================================

if __name__ == "__main__":
    main()
