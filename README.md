# Holdsport MVP Bot 🤖

Et simpelt Python-script, der automatisk tilmelder dig aktiviteter på Holdsport – med fokus på ét specifikt hold og aktivitet. Scriptet kan køre kontinuerligt (f.eks. via Railway eller cron job) og sender notifikationer via Telegram, når du bliver tilmeldt.

## 🔧 Funktioner

- Logger ind via Holdsport API
- Henter dine hold og deres aktiviteter de næste 8 dage
- Finder aktiviteter med navnet `Herre 3 træning` (kan tilpasses)
- Tjekker om du allerede er tilmeldt – ellers tilmelder den dig
- Sender notifikation via Telegram, når du bliver tilmeldt
- Sikker: forsøger **aldrig** at afmelde eller ændre eksisterende tilmeldinger
- Kan køre som cron job eller kontinuerligt i fx Railway

## 🚀 Kom i gang

### 1. Clone repo

```bash
git clone https://github.com/stffnvlldsn/holdsport-mvp.git
cd holdsport-mvp
```

### 2. Installer afhængigheder

```bash
pip install -r requirements.txt
```

### 3. Opret `.env`-fil

Opret en `.env` i roden med følgende indhold:

```dotenv
HOLDSPORT_USERNAME=din@mail.dk
HOLDSPORT_PASSWORD=ditpassword
HOLDSPORT_ACTIVITY_NAME=Herre 3 træning
DAYS_AHEAD=7
CHECK_INTERVAL=600  # sekunder mellem hver tjek (fx 600 = 10 minutter)
TELEGRAM_BOT_TOKEN=din_telegram_bot_token
TELEGRAM_CHAT_ID=dit_telegram_chat_id
```

> `HOLDSPORT_ACTIVITY_NAME` er navnet på aktiviteten (case-insensitive)  
> `DAYS_AHEAD` = hvor langt frem i tiden der skal tjekkes  
> `CHECK_INTERVAL` = hvor ofte scriptet skal tjekke (i sekunder)

### 4. Start script

```bash
python main.py
```

## 🖥️ Hosting

**Anbefalet:** Kør scriptet gratis og kontinuerligt via [Railway](https://railway.app) som baggrundsservice – ingen behov for server eller cron setup.

Andre muligheder:

- Cron job (lokalt eller server)
- AWS Lambda (kræver lidt tilpasning)
- Docker container (ekstra fleksibilitet)

## 🔒 Sikkerhed

- Scriptet **tilmelder kun** – det vil aldrig forsøge at afmelde eller ændre tilmelding
- Logger alle aktiviteter og beslutninger i terminalen
- Telegram bruges til notifikationer for at holde dig opdateret

## 🧠 Inspiration & TODOs

- Web UI til status og logs
- Støtte flere aktiviteter
- Discord notifikationer
- Retry-logic ved fejl
- Deployment som Docker-image

## 📄 Licens

MIT License

---

Bygget med ❤️ af [@stffnvlldsn](https://github.com/stffnvlldsn)
