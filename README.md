# rss-telegram-bot
# RSS Feed Monitor con Instagram 📡📸

Monitor RSS feeds e account Instagram inviando notifiche in tempo reale su Telegram. Soluzione completamente **GRATUITA** usando RSSHub.

## ✨ Caratteristiche

- 📰 **Feed RSS tradizionali** (Google Alerts, siti web, blog)
- 📸 **Instagram** tramite RSSHub (gratuito, senza API)
- 🐦 **Twitter/X** tramite RSSHub  
- 📺 **YouTube** tramite RSSHub
- 🤖 **Reddit** tramite RSSHub
- 📱 **Notifiche Telegram** con formatting HTML
- 💾 **Persistenza dati** (non invia duplicati)
- 🔄 **Monitoraggio continuo** con intervalli configurabili
- ⚡ **Failover automatico** tra istanze RSSHub
- 🆓 **Completamente gratuito**

## 🚀 Quick Start

### 1. Clone del repository
```bash
git clone https://github.com/tuousername/rss-telegram-monitor.git
cd rss-telegram-monitor
```

### 2. Installazione dipendenze
```bash
pip install -r requirements.txt
```

### 3. Configurazione Telegram

#### Crea un bot Telegram:
1. Scrivi a [@BotFather](https://t.me/BotFather) su Telegram
2. Invia `/newbot` e segui le istruzioni
3. Salva il **token** che ti viene fornito

#### Ottieni il Chat ID:
1. Scrivi al tuo bot appena creato
2. Invia `/start`
3. Visita: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Cerca il campo `"chat":{"id":123456789}`

### 4. Configurazione del monitor

Crea un file `config.json`:
```json
{
  "telegram_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "telegram_chat_id": "123456789",
  "intervallo_controllo": 600
}
```

**Alternativa - variabili d'ambiente:**
```bash
export TELEGRAM_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"
export INTERVALLO_CONTROLLO="600"
```

### 5. Avvio
```bash
python rss_monitor.py
```

## ⚙️ Configurazione Feed

Modifica la lista `FEEDS_DA_MONITORARE` nel file `rss_monitor.py`:

```python
FEEDS_DA_MONITORARE = [
    # RSS tradizionali
    {
        "name": "Tech News",
        "emoji": "💻",
        "url": "https://feeds.feedburner.com/TechCrunch",
        "type": "rss"
    },
    
    # Instagram (sostituisci 'username' con l'account desiderato)
    {
        "name": "Instagram - NASA",
        "emoji": "🚀",
        "url": "https://rsshub.app/instagram/user/nasa",
        "type": "instagram"
    },
    
    # Twitter
    {
        "name": "Twitter - @elonmusk",
        "emoji": "🐦", 
        "url": "https://rsshub.app/twitter/user/elonmusk",
        "type": "twitter"
    },
    
    # YouTube
    {
        "name": "YouTube - Veritasium",
        "emoji": "📺",
        "url": "https://rsshub.app/youtube/user/@veritasium",
        "type": "youtube"
    },
    
    # Reddit
    {
        "name": "Reddit - r/Python",
        "emoji": "🐍",
        "url": "https://rsshub.app/reddit/r/Python",
        "type": "reddit"
    }
]
```

## 📱 Instagram Setup

Per monitorare account Instagram **gratuitamente**:

1. **Trova l'username** dell'account che vuoi monitorare
2. **Aggiungi alla configurazione**:
   ```python
   {
       "name": "Instagram - nomeutente",
       "emoji": "📸",
       "url": "https://rsshub.app/instagram/user/nomeutente",
       "type": "instagram"
   }
   ```
3. **Il monitor inizierà automaticamente** a controllare i nuovi post

### Esempi di account Instagram popolari:
- `nasa` - NASA
- `natgeo` - National Geographic  
- `therock` - Dwayne Johnson
- `cristiano` - Cristiano Ronaldo
- `arianagrande` - Ariana Grande

## 🛠️ Deploy

### Server Linux/VPS
```bash
# Clone e setup
git clone https://github.com/tuousername/rss-telegram-monitor.git
cd rss-telegram-monitor
pip install -r requirements.txt

# Configurazione
nano config.json

# Avvio in background
nohup python rss_monitor.py &
```

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "rss_monitor.py"]
```

```bash
docker build -t rss-monitor .
docker run -d --name rss-monitor rss-monitor
```

### Raspberry Pi
```bash
# Installazione
sudo apt update
sudo apt install python3-pip git
git clone https://github.com/tuousername/rss-telegram-monitor.git
cd rss-telegram-monitor
pip3 install -r requirements.txt

# Auto-avvio con systemd
sudo nano /etc/systemd/system/rss-monitor.service
```

## 🔧 Troubleshooting

### Instagram non funziona?
- ✅ Verifica che l'username sia corretto
- ✅ Alcuni account privati potrebbero non funzionare
- ✅ RSSHub ha limitazioni di rate, riprova più tardi
- ✅ Prova un'istanza RSSHub diversa (il codice fa failover automatico)

### Errori di connessione?
- ✅ Controlla la connessione internet
- ✅ Verifica che il token Telegram sia corretto
- ✅ Alcuni feed potrebbero essere temporaneamente non disponibili

### Rate limiting Telegram?
- ✅ Il codice include pause automatiche tra i messaggi
- ✅ Riduci la frequenza di controllo se necessario

## 📖 RSSHub - Servizi supportati

[RSSHub](https://docs.rsshub.app/) supporta centinaia di servizi:

- **Social:** Instagram, Twitter, Facebook, TikTok, LinkedIn
- **Video:** YouTube, Vimeo, Bilibili
- **News:** BBC, CNN, Reuters, Associated Press  
- **Tech:** GitHub, Stack Overflow, Hacker News
- **Shopping:** Amazon, eBay
- **E tanto altro...**

Consulta la [documentazione RSSHub](https://docs.rsshub.app/) per tutti i servizi disponibili.

## 🤝 Contribuire

1. Fork del progetto
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push del branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT - vedi il file [LICENSE](LICENSE) per i dettagli.

## ⭐ Supporta il progetto

Se questo progetto ti è utile:
- ⭐ Metti una stella su GitHub
- 🍴 Fai un fork e contribuisci
- 🐛 Segnala bug o richiedi feature
- 📢 Condividi con altri sviluppatori

## 📞 Contatti

- GitHub Issues: [Issues](https://github.com/tuousername/rss-telegram-monitor/issues)
- Telegram: [@tuousername](https://t.me/tuousername)

---

**Made with ❤️ and Python**
