#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test invio diretto - Verifica se i messaggi arrivano
"""

import requests
import time

TOKEN = "8358394281:AAHUUZeDWKSTpu0IP1dnYUanuvlwpiLRSNA"
CHAT_ID = "-4942650093"

def test_invio():
    print("🧪 TEST INVIO DIRETTO TELEGRAM")
    print("=" * 60)
    
    # Test 1: Messaggio semplice
    print("\n📤 Test 1: Invio messaggio semplice...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    payload = {
        'chat_id': CHAT_ID,
        'text': 'Test messaggio #1 - Testo semplice'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        
        data = response.json()
        print(f"   Response: {data}")
        
        if response.status_code == 200 and data.get('ok'):
            print("   ✅ Messaggio 1 inviato!")
        else:
            print(f"   ❌ Errore: {data.get('description', 'Sconosciuto')}")
            
            # Analizza errore
            desc = data.get('description', '').lower()
            if 'not found' in desc or 'chat not found' in desc:
                print("\n   🔍 PROBLEMA TROVATO: Chat ID errato o bot non nel gruppo")
                print(f"   Il Chat ID che stai usando è: {CHAT_ID}")
                print("\n   📝 Come ottenere il Chat ID corretto:")
                print("   1. Aggiungi @userinfobot al gruppo")
                print("   2. Lui ti dirà il Chat ID corretto")
                print("   3. Oppure usa @RawDataBot")
            elif 'blocked' in desc:
                print("\n   🔍 PROBLEMA: Bot bloccato dall'utente/gruppo")
            elif 'kicked' in desc:
                print("\n   🔍 PROBLEMA: Bot rimosso dal gruppo")
            elif 'need administrator rights' in desc or 'not enough rights' in desc:
                print("\n   🔍 PROBLEMA: Bot non ha permessi sufficienti")
                print("   Se è un canale, rendilo amministratore")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Errore connessione: {e}")
        return False
    
    time.sleep(2)
    
    # Test 2: Messaggio HTML
    print("\n📤 Test 2: Invio messaggio HTML...")
    payload = {
        'chat_id': CHAT_ID,
        'text': '✅ <b>Test messaggio #2</b>\n\n<i>Formattazione HTML</i>',
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Messaggio 2 inviato!")
        else:
            data = response.json()
            print(f"   ❌ Errore: {data.get('description', 'Sconosciuto')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    time.sleep(2)
    
    # Test 3: Messaggio con link
    print("\n📤 Test 3: Invio messaggio con link...")
    payload = {
        'chat_id': CHAT_ID,
        'text': '🔗 <b>Test messaggio #3</b>\n\nLink: https://www.google.com',
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Messaggio 3 inviato!")
        else:
            data = response.json()
            print(f"   ❌ Errore: {data.get('description', 'Sconosciuto')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ TUTTI I TEST COMPLETATI!")
    print("🎉 Controlla Telegram - dovresti aver ricevuto 3 messaggi!")
    print("=" * 60)
    return True

def verifica_chat_id():
    """Verifica info sulla chat."""
    print("\n🔍 Verifica Chat ID...")
    url = f"https://api.telegram.org/bot{TOKEN}/getChat"
    
    try:
        response = requests.get(url, params={'chat_id': CHAT_ID}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                chat = data['result']
                print(f"   ✅ Chat trovata!")
                print(f"   ID: {chat.get('id')}")
                print(f"   Tipo: {chat.get('type')}")
                print(f"   Titolo: {chat.get('title', 'N/A')}")
                
                # Verifica permessi bot
                if chat.get('type') in ['group', 'supergroup']:
                    print(f"\n   📋 Info gruppo:")
                    print(f"   Membri: {chat.get('member_count', 'N/A')}")
                    
                    # Verifica se il bot è amministratore
                    admin_url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
                    admin_response = requests.get(
                        admin_url, 
                        params={'chat_id': CHAT_ID, 'user_id': TOKEN.split(':')[0]},
                        timeout=10
                    )
                    
                    if admin_response.status_code == 200:
                        admin_data = admin_response.json()
                        if admin_data.get('ok'):
                            member_info = admin_data['result']
                            status = member_info.get('status')
                            print(f"   Status bot: {status}")
                            
                            if status == 'left':
                                print(f"   ⚠️ Il bot ha LASCIATO il gruppo!")
                                print(f"   Aggiungilo di nuovo")
                            elif status == 'kicked':
                                print(f"   ⚠️ Il bot è stato RIMOSSO!")
                                print(f"   Aggiungilo di nuovo")
                            elif status == 'restricted':
                                print(f"   ⚠️ Il bot ha RESTRIZIONI!")
                                print(f"   Controlla i permessi")
                            elif status in ['member', 'administrator', 'creator']:
                                print(f"   ✅ Il bot è nel gruppo!")
                                
                                # Verifica permessi di scrittura
                                can_send = member_info.get('can_send_messages', True)
                                print(f"   Può inviare messaggi: {can_send}")
                                
                                if not can_send:
                                    print(f"   ⚠️ Il bot NON può inviare messaggi!")
                                    print(f"   Dagli il permesso di scrivere")
                return True
            else:
                print(f"   ❌ Errore: {data.get('description')}")
        else:
            print(f"   ❌ HTTP {response.status_code}")
            data = response.json()
            print(f"   Errore: {data.get('description', 'Sconosciuto')}")
            
        return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False

def trova_chat_id_reale():
    """Cerca il vero Chat ID dai messaggi recenti."""
    print("\n🔍 Cerco Chat ID reale dai messaggi recenti...")
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            updates = data.get('result', [])
            
            if not updates:
                print("   📭 Nessun messaggio recente trovato")
                print("\n   💡 Fai questo:")
                print("   1. Apri il gruppo su Telegram")
                print("   2. Scrivi un messaggio qualsiasi")
                print("   3. Riesegui questo script")
                return
            
            print(f"   📨 Trovati {len(updates)} messaggi")
            
            # Trova tutte le chat uniche
            chats_trovate = {}
            for update in updates:
                msg = update.get('message', {}) or update.get('my_chat_member', {})
                chat = msg.get('chat', {})
                chat_id = chat.get('id')
                
                if chat_id and chat_id not in chats_trovate:
                    chats_trovate[chat_id] = {
                        'id': chat_id,
                        'type': chat.get('type'),
                        'title': chat.get('title', chat.get('first_name', 'N/A'))
                    }
            
            if chats_trovate:
                print("\n   📋 Chat trovate:")
                for i, (cid, info) in enumerate(chats_trovate.items(), 1):
                    print(f"\n   {i}. Chat ID: {cid}")
                    print(f"      Tipo: {info['type']}")
                    print(f"      Nome: {info['title']}")
                    
                    if str(cid) == str(CHAT_ID):
                        print(f"      ✅ QUESTO è il Chat ID che stai usando!")
                    else:
                        print(f"      ⚠️ Questo è DIVERSO da quello configurato ({CHAT_ID})")
                
                print("\n   💡 Se il tuo gruppo ha un ID diverso, aggiornalo nel codice!")
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")

if __name__ == "__main__":
    # Verifica chat
    verifica_chat_id()
    
    print()
    input("⏸️  Premi INVIO per continuare con i test di invio...")
    
    # Test invio
    success = test_invio()
    
    if not success:
        print("\n💡 I messaggi non sono stati inviati.")
        trova_chat_id_reale()
    
    print("\n👋 Test completato!")
