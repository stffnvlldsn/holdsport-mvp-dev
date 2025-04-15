import os
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE = "https://api.holdsport.dk/v1"
USERNAME = os.getenv("HOLDSPORT_USERNAME")
PASSWORD = os.getenv("HOLDSPORT_PASSWORD")
ACTIVITY_NAME = os.getenv("HOLDSPORT_ACTIVITY_NAME", "Herre 3 træning").strip().lower()
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "7"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "180"))

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
        print("⛔ Ingen sikker tilmeldingshandling fundet – springer over.")
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
            print("🎉 Succes! Du er nu tilmeldt Herre 3 træning.")
            return True
        else:
            print(f"❌ Tilmelding fejlede – statuskode {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"[Fejl] Ved tilmelding: {e}")
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

                print(f"✅ Fundet aktivitet: {activity['name']} på holdet {team_name}")
                print(f"  ➤ Starttid: {activity.get('starttime', 'Ukendt')}")
                print(f"  ➤ Lokation: {activity.get('place', 'Ukendt')}")

                # Allerede tilmeldt?
                status_raw = activity.get("status", "")
                status = str(status_raw).lower()
                if status == "tilmeldt":
                    print("ℹ️ Du er allerede tilmeldt.")
                    return
                else:
                    print("🟡 Forsøger at tilmelde dig...")
                    signup_for_activity(activity)
                    return
    except requests.RequestException as e:
        print(f"[Fejl] API-kald fejlede: {e}")

def main():
    print("🤖 Starter Holdsport-bot med tilmelding...\n")
    while True:
        print("🔍 Tjekker Holdsport for aktiviteter...\n")
        fetch_activities()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
