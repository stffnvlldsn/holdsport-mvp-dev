# Changelog

Alle større ændringer og forbedringer for Holdsport MVP-projektet.

## [v1.0.0] - 2025-04-18
### Added
- Første version af scriptet til automatisk tilmelding på Holdsport.dk.
- Login via Holdsport API med miljøvariabler.
- Automatisk scanning af alle hold og aktiviteter de næste 7 dage.
- Tilmelding til aktiviteter med navnet "Herre 3 træning".
- Telegram notifikation ved succesfuld tilmelding.
- Logging til terminal og fil (`holdsport.log`).
- Konfigurerbar `DAYS_AHEAD`, `CHECK_INTERVAL` og `ACTIVITY_NAME`.

### Deployment
- Kører som cron-lignende job hvert 10. minut via Railway.
- Brug af GitHub + Cursor for udvikling og versionsstyring.

### Security
- Miljøvariabler tilføjet via `.env` og Railway Environment Settings.
- Sikring mod utilsigtet afmelding eller ændringer.

