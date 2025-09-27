# rss-telegram-bot
# RSS Feed Monitor con Instagram 📡📸

# 🔧 Guida Setup Dettagliata

Guida passo-passo per configurare il RSS Feed Monitor su GitHub Actions.

## 📋 Prerequisiti

- Account GitHub (gratuito)
- Account Telegram (gratuito)
- 10 minuti di tempo

## 🤖 Step 1: Crea il Bot Telegram

### 1.1 Apri Telegram
- Desktop: [web.telegram.org](https://web.telegram.org)
- Mobile: App Telegram

### 1.2 Contatta BotFather
1. Cerca `@BotFather` nella ricerca di Telegram
2. Avvia la conversazione cliccando **START**

### 1.3 Crea il Bot
1. Invia `/newbot`
2. BotFather chiede il **nome del bot**:
   ```
   Scegli un nome, ad esempio: "Il Mio RSS Monitor"
   ```
3. BotFather chiede lo **username del bot** (deve finire con 'bot'):
   ```
   Esempio: mio_rss_monitor_bot
   ```
4. **SALVA IL TOKEN** che ricevi:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-ESEMPIO
   ```

### 1.4 Ottieni Chat ID
1. Scrivi al bot appena creato (clicca sul link che ti ha dato BotFather)
2. Invia `/start` al tuo bot
3. Apri questo link nel browser (sostituisci IL_TUO_TOKEN):
   ```
   https://api.telegram.org/botIL_TUO_TOKEN/getUpdates
   ```
4. Cerca nel JSON una riga simile a:
   ```json
   "chat":{"id":123456789,"first_name":"TuoNome"
   ```
5. **SALVA IL NUMERO** (123456789 nell'esempio)

## 📁 Step 2: Fork il Repository

### 2.1 Fork
1. Vai su [GitHub Repository](https://github.com/tuousername/rss-telegram-monitor)
2. Clicca **Fork** in alto a destra
3. Conferma creando il fork nel tuo account

### 2.2 Verifica Fork
- Ora hai una copia in: `https://github.com/TUOUSERNAME/rss-telegram-monitor`

## 🔐 Step 3: Configura Secrets

### 3.1 Accedi ai Settings
1. Nel TUO repository forkato, clicca **Settings**
2. Nel menu a sinistra: **Secrets and variables** > **Actions**

### 3.2 Aggiungi TELEGRAM_TOKEN
1. Clicca **New repository secret**
2. Nome: `TELEGRAM_TOKEN`
3. Valore: Il token che hai salvato (esempio: `1234567890:ABCdefGHI...`)
4. Clicca **Add secret**

### 3.3 Aggiungi TELEGRAM_CHAT_ID
1. Clicca **New repository secret**  
2. Nome: `TELEGRAM_CHAT_ID`
3. Valore: Il chat ID che hai salvato (esempio: `123456789`)
4. Clicca **Add secret**

### 3.4 Verifica Secrets
Dovresti vedere 2 secrets:
- ✅ TELEGRAM_TOKEN
- ✅ TELEGRAM_CHAT_ID

## ⚙️ Step 4: Personalizza Feed

### 4.1 Modifica github_monitor.py
1. Nel tuo repository, clicca sul file `github_monitor.py`
2. Clicca l'icona ✏️ (Edit this file)

### 4.2 Trova la sezione FEEDS_DA_MONITORARE
```python
FEEDS_DA_MONITORARE = [
    # I tuoi feed esistenti...
```

### 4.3 Aggiungi Instagram
Per aggiungere account Instagram, aggiungi:
```python
{
    "name": "Instagram - NASA", 
    "emoji": "🚀",
    "url": "https://rsshub.app/instagram/user/nasa",
    "type": "instagram"
},
{
    "name": "Instagram - National Geographic",
    "emoji": "📸", 
    "url": "https://rsshub.app/instagram/user/natgeo",
    "type": "instagram"
}
```

### 4.4 Account Instagram Popolari da Provare
```python
# Celebrità
"cristiano"      # Cristiano Ronaldo
"therock"        # Dwayne Johnson  
"kyliejenner"    # Kylie Jenner
"selenagomez"    # Selena Gomez

# Scienza e Tecnologia
"nasa"           # NASA
"spacex"         # SpaceX
"natgeo"         # National Geographic
"tesla"          # Tesla

# Brand e Aziende  
"apple"          # Apple
"nike"           # Nike
"cocacola"       # Coca Cola
```

### 4.5 Salva le Modifiche
1. Scorri in basso
2. Scrivi un messaggio commit: `"Aggiunti account Instagram"`
3. Clicca **Commit changes**

## 🚀 Step 5: Attiva GitHub Actions

### 5.1 Vai alla Tab Actions
1. Nel tuo repository, clicca **Actions**
2. Se vedi "Workflows aren't being run on this forked repository"
3. Clicca **"I understand my workflows, go ahead and enable them"**

### 5.2 Prima Esecuzione Manuale
1. Clicca su **RSS Feed Monitor** (il workflow)
2. Clicca **Run workflow** > **Run workflow**
3. Aspetta ~30 secondi

### 5.3 Controlla i Log
1. Clicca sull'esecuzione appena avviata
2. Clicca **monitor** > **Run RSS Monitor**
3. Dovresti vedere:
   ```
   📂 Caricati 0 link già processati
   🔍 Controllo instagram: Instagram - NASA
   🆕 Trovati X nuovi contenuti...
   ✅ Messaggio inviato su Telegram
   ```

## 📱 Step 6: Test e Verifica

### 6.1 Controlla Telegram
- Dovresti ricevere notifiche dal tuo bot
- Formato esempio:
  ```
  🚀 Instagram - NASA
  
  📸 Nuovo post Instagram
  📝 Amazing photo from space...
  
  🔗 https://instagram.com/p/xyz
  ```

### 6.2 Verifica Stato Salvato
1. Nel repository, dovresti vedere un nuovo file `visti.json`
2. Contiene i link già processati per evitare duplicati

### 6.3 Esecuzione Automatica
- Il workflow ora girerà automaticamente ogni 10 minuti
- Controlla la tab Actions per vedere le esecuzioni

## 🔧 Step 7: Personalizzazione Avanzata

### 7.1 Cambiare Frequenza
Nel file `.github/workflows/monitor.yml`:

```yaml
schedule:
  - cron: '*/5 * * * *'   # Ogni 5 minuti
  - cron: '*/15 * * * *'  # Ogni 15 minuti  
  - cron: '0 * * * *'     # Ogni ora
  - cron: '0 */6 * * *'   # Ogni 6 ore
```

### 7.2 Aggiungere Twitter
```python
{
    "name": "Twitter - Elon Musk",
    "emoji": "🐦",
    "url": "https://rsshub.app/twitter/user/elonmusk", 
    "type": "twitter"
}
```

### 7.3 Aggiungere YouTube
```python
{
    "name": "YouTube - MrBeast",
    "emoji": "📺",
    "url": "https://rsshub.app/youtube/user/@MrBeast",
    "type": "youtube"
}
```

### 7.4 Aggiungere Reddit
```python
{
    "name": "Reddit - r/Python",
    "emoji": "🐍",
    "url": "https://rsshub.app/reddit/r/Python", 
    "type": "reddit"
}
```

## 🐛 Troubleshooting

### ❌ Problema: Nessuna notifica ricevuta

**Controlli:**
1. Verifica Secrets in Settings > Secrets and variables > Actions
2. Controlla log in Actions per errori
3. Testa bot manualmente inviando messaggio

**Soluzioni:**
- Re-crea i Secrets se necessario
- Verifica che il bot sia attivo
- Controlla formato Chat ID (solo numeri)

### ❌ Problema: Instagram non funziona

**Possibili cause:**
- Account Instagram privato (non supportato)
- RSSHub temporaneamente down
- Username Instagram errato

**Soluzioni:**
- Prova account pubblico famoso: `nasa`, `natgeo`
- Attendi qualche ora e riprova
- Verifica username su Instagram web

### ❌ Problema: GitHub Actions fallisce

**Controlli:**
1. Actions abilitato? (Settings > Actions > General)
2. Repository pubblico o privato? (Privato ha limiti)
3. Errori nei log di Actions?

**Soluzioni:**
- Abilita Actions se disabilitato
- Per repository privati, verifica limiti GitHub
- Leggi errore specifico nei log

### ❌ Problema: Troppe esecuzioni fallite

**Causa comune:** Rate limiting RSSHub

**Soluzione:**
- Riduci frequenza esecuzione (ogni 15-30 minuti)
- Rimuovi feed problematici temporaneamente
- Il sistema ha failover automatico per RSSHub

## 📊 Monitoraggio Uso GitHub Actions

### Controllare Minuti Utilizzati
1. GitHub > Settings > Billing and plans
2. Vedi "Actions minutes used"
3. Limite gratuito: 2000 minuti/mese

### Consumo Stimato
- **Ogni 10 min:** ~1 minuto di compute
- **Al mese:** ~720 minuti (con 5-10 feed)
- **Margine:** Puoi fare 2-3 progetti simili

### Ottimizzare Consumo
- Riduci frequenza se non serve spesso
- Limita numero di feed monitorati
- Disabilita temporaneamente se non usi

## 🎯 Consigli Best Practice

### 🔹 Sicurezza
- Mai committare token in chiaro nel codice
- Usa sempre GitHub Secrets
- Rigenera token se compromessi

### 🔹 Performance  
- Max 20-30 feed per progetto
- Frequenza ragionevole (10-15 minuti)
- Monitora log per errori ricorrenti

### 🔹 Manutenzione
- Controlla periodicamente feed rotti
- Aggiorna RSSHub URLs se cambiano
- Pulisci feed non più interessanti

## ✅ Checklist Finale

Dopo aver completato setup:

- [ ] ✅ Bot Telegram creato e token salvato
- [ ] ✅ Chat ID ottenuto e salvato  
- [ ] ✅ Repository forkato
- [ ] ✅ Secrets configurati (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
- [ ] ✅ Feed personalizzati nel codice
- [ ] ✅ GitHub Actions abilitato
- [ ] ✅ Prima esecuzione manuale testata
- [ ] ✅ Notifiche Telegram ricevute
- [ ] ✅ File visti.json creato automaticamente
- [ ] ✅ Esecuzione automatica ogni 10 minuti attiva

## 🎉 Complimenti!

Il tuo RSS Feed Monitor con Instagram è ora attivo e funzionante su GitHub Actions!

**Cosa succede ora:**
- ⏰ Controllo automatico ogni 10 minuti
- 📱 Notifiche Telegram immediate  
- 💾 Stato persistente per evitare duplicati
- 🔄 Esecuzione continua 24/7 gratis

**Prossimi passi:**
- Aggiungi più account Instagram interessanti
- Sperimenta con Twitter, YouTube, Reddit
- Condividi il progetto con amici
- Contribuisci miglioramenti su GitHub

---

**Hai domande?** Apri una Issue nel repository GitHub!
