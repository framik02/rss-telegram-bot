#!/usr/bin/env python3
# -- coding: utf-8 --
"""
RSS Feed Monitor con notifiche Telegram
Monitora feed RSS e invia notifiche su Telegram per nuovi contenuti
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
TELEGRAM_TOKEN = "8358394281:AAHUUZeDWKSTpu0IP1dnYUanuvlwpiLRSNA"

# Chat ID dove inviare i messaggi (ottienilo scrivendo al bot e usando /start)
TELEGRAM_CHAT_ID = "6129973289"

# File per salvare i link già inviati
FILE_VISTI = "visti.json"

# Tempo di attesa tra i controlli (in secondi) - 600 = 10 minuti
INTERVALLO_CONTROLLO = 600

# Lista dei feed RSS da monitorare
FEEDS_RSS = [
    {
        "name": "Bellucci",
        "emoji": "📢",
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/16829576264885656380"
    },
    {
        "name": "Ministero",
        "emoji": "🚀",
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/16156285375326995850"
    },
    {
        "name": "Bellucci",
        "emoji": "🔬",
        "url": "https://www.google.com/alerts/feeds/03387377238691625601/1110300614940787881"
    }
    # Aggiungi altri feed qui seguendo lo stesso formato
]

# ================================
# FUNZIONI UTILITY
# ================================

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

def invia_messaggio_telegram(messaggio):
    """
    Invia un messaggio tramite l'API di Telegram.

    Args:
        messaggio (str): Il testo del messaggio da inviare

    Returns:
        bool: True se l'invio è riuscito, False altrimenti
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': messaggio,
        'parse_mode': 'HTML',  # Permette formatting HTML
        'disable_web_page_preview': False  # Mostra l'anteprima dei link
    }

    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()

        print(f"✅ Messaggio inviato su Telegram")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nell'inviare messaggio Telegram: {e}")
        return False

def controlla_feed_rss(feed_info, link_visti):
    """
    Controlla un singolo feed RSS per nuovi contenuti.

    Args:
        feed_info (dict): Informazioni del feed (name, emoji, url)
        link_visti (set): Set dei link già processati

    Returns:
        list: Lista dei nuovi link trovati
    """
    nuovi_link = []

    try:
        print(f"🔍 Controllo feed: {feed_info['name']}")

        # Scarica e parsa il feed RSS
        feed = feedparser.parse(feed_info['url'])

        if feed.bozo:
            print(f"⚠  Warning: feed malformato per {feed_info['name']}")

        # Controlla ogni entry nel feed
        for entry in feed.entries:
            # Usa il link come identificativo unico
            link = getattr(entry, 'link', '')

            if not link:
                continue

            # Se il link non è mai stato visto, è nuovo
            if link not in link_visti:
                titolo = getattr(entry, 'title', 'Titolo non disponibile')

                # Crea il messaggio formattato
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

                # Aggiungi il link ai visti
                link_visti.add(link)

        if nuovi_link:
            print(f"🆕 Trovati {len(nuovi_link)} nuovi contenuti in {feed_info['name']}")
        else:
            print(f"📭 Nessun nuovo contenuto in {feed_info['name']}")

    except Exception as e:
        print(f"❌ Errore nel controllare feed {feed_info['name']}: {e}")

    return nuovi_link

def main():
    """
    Funzione principale che esegue il monitoraggio continuo.
    """
    print("🤖 Avvio RSS Feed Monitor per Telegram")
    print(f"⏰ Controllo ogni {INTERVALLO_CONTROLLO//60} minuti")
    print(f"📋 Monitoraggio {len(FEEDS_RSS)} feed RSS")
    print("-" * 50)

    # Verifica configurazione
    if TELEGRAM_TOKEN == "IL_TUO_TOKEN_QUI" or TELEGRAM_CHAT_ID == "IL_TUO_CHAT_ID_QUI":
        print("❌ ERRORE: Devi configurare TELEGRAM_TOKEN e TELEGRAM_CHAT_ID!")
        print("1. Ottieni il token da @BotFather su Telegram")
        print("2. Ottieni il chat_id scrivendo al tuo bot")
        return

    # Carica i link già visti
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

            # Controlla ogni feed RSS
            for feed_info in FEEDS_RSS:
                nuovi_link = controlla_feed_rss(feed_info, link_visti)

                # Invia ogni nuovo contenuto trovato
                for contenuto in nuovi_link:
                    if invia_messaggio_telegram(contenuto['messaggio']):
                        nuovi_contenuti_totali += 1
                        # Piccola pausa tra i messaggi per evitare rate limiting
                        time.sleep(1)
                    else:
                        # Se l'invio fallisce, rimuovi il link dai visti per ritentare
                        link_visti.discard(contenuto['link'])

            # Salva i link visti aggiornati
            if nuovi_contenuti_totali > 0:
                salva_link_visti(link_visti)
                print(f"📤 Inviati {nuovi_contenuti_totali} nuovi contenuti")
            else:
                print("😴 Nessun nuovo contenuto trovato")

            print(f"⏳ Prossimo controllo tra {INTERVALLO_CONTROLLO//60} minuti...")
            time.sleep(INTERVALLO_CONTROLLO)

    except KeyboardInterrupt:
        print("\n\n⏹  Interruzione manuale rilevata")
        salva_link_visti(link_visti)
        print("💾 Link visti salvati prima della chiusura")
        print("👋 RSS Feed Monitor terminato")

    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        salva_link_visti(link_visti)
        print("💾 Link visti salvati prima della chiusura")

# ================================
# AVVIO PROGRAMMA
# ================================

if _name_ == "_main_":
    main()
