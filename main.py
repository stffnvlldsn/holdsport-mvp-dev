import os
import requests
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import telegram

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('holdsport.log')
    ]
)

# Load environment variables
load_dotenv()

API_BASE = "https://api.holdsport.dk/v1"
USERNAME = os.getenv("HOLDSPORT_USERNAME")
PASSWORD = os.getenv("HOLDSPORT_PASSWORD")
ACTIVITY_NAME = os.getenv("HOLDSPORT_ACTIVITY_NAME", "Herre 3 træning").strip().lower()
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "8"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "180"))

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_notification(message):
    """Send a notification via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("⚠️ Telegram credentials not configured", logging.WARNING)
        return
    
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        log_message("✅ Telegram notification sent successfully")
    except Exception as e:
        log_message(f"❌ Failed to send Telegram notification: {e}", logging.ERROR)

def log_message(message, level=logging.INFO):
    logging.log(level, message)

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers.update({
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Holdsport-MVP/1.0"
})

def is_signup_action_safe(activity):
    """Sikrer at vi *kun* tilmelder os aktiviteter – aldrig afmelder eller ændrer"""
    for action in activity.get("actions", []):
        user_action = action.get("activities_user", {})
        if user_action.get("name", "").lower() == "tilmeld":
            return True
    return False

def signup_for_activity(activity):
    if not is_signup_action_safe(activity):
        log_message("⛔ Ingen sikker tilmeldingshandling fundet – springer over.")
        return False

    action_path = activity["action_path"]
    if action_path.startswith("/v1"):
        action_path = action_path[3:]

    data = {
        "activities_user": {
            "joined_status": 1,
            "picked": 1
        }
    }

    try:
        response = session.request(
            method=activity["action_method"],
            url=f"{API_BASE}{action_path}",
            json=data
        )
        if response.status_code in [200, 201]:
            success_message = f"🎉 Succes! Du er nu tilmeldt {activity.get('name', 'Herre 3 træning')}.\n" \
                            f"📅 Dato: {activity.get('starttime', 'Ukendt')}\n" \
                            f"📍 Lokation: {activity.get('place', 'Ukendt')}"
            log_message(success_message)
            send_telegram_notification(success_message)
            return True
        else:
            log_message(f"❌ Tilmelding fejlede – statuskode {response.status_code}", logging.ERROR)
            return False
    except requests.RequestException as e:
        log_message(f"[Fejl] Ved tilmelding: {e}", logging.ERROR)
        return False

def fetch_activities():
    try:
        teams_res = session.get(f"{API_BASE}/teams")
        teams_res.raise_for_status()
        teams = teams_res.json()

        for team in teams:
            team_id = team["id"]
            team_name = team["name"]

            today = datetime.now()
            end_date = today + timedelta(days=DAYS_AHEAD)
            params = {
                "date": today.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }

            act_res = session.get(f"{API_BASE}/teams/{team_id}/activities", params=params)
            act_res.raise_for_status()
            activities = act_res.json()

            for activity in activities:
                name = activity.get("name", "").strip().lower()

                # 🎯 Fokuser kun på Herre 3 træning
                if name != ACTIVITY_NAME:
                    continue

                log_message(f"✅ Fundet aktivitet: {activity['name']} på holdet {team_name}")
                log_message(f"  ➤ Starttid: {activity.get('starttime', 'Ukendt')}")
                log_message(f"  ➤ Lokation: {activity.get('place', 'Ukendt')}")

                # Allerede tilmeldt?
                status_raw = activity.get("status", "")
                status = str(status_raw).lower()
                if status == "tilmeldt":
                    log_message("ℹ️ Du er allerede tilmeldt.")
                    return
                else:
                    log_message("🟡 Forsøger at tilmelde dig...")
                    signup_for_activity(activity)
                    return
    except requests.RequestException as e:
        log_message(f"[Fejl] API-kald fejlede: {e}", logging.ERROR)

def main():
    log_message("🤖 Starter Holdsport-bot med tilmelding...")
    while True:
        try:
            log_message("🔍 Tjekker Holdsport for aktiviteter...")
            fetch_activities()
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            log_message(f"Uventet fejl: {e}", logging.ERROR)
            time.sleep(60)  # Vent 1 minut ved uventede fejl

if __name__ == "__main__":
    main()
