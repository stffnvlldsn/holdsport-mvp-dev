import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.holdsport.dk/v1"
USERNAME = os.getenv("HOLDSPORT_USERNAME")
PASSWORD = os.getenv("HOLDSPORT_PASSWORD")
ACTIVITY_NAME = os.getenv("HOLDSPORT_ACTIVITY_NAME", "Herre 3 træning")

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers.update({
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Holdsport-MVP/1.0"
})

def get_teams():
    response = session.get(f"{API_BASE}/teams")
    response.raise_for_status()
    return response.json()

def get_activities(team_id):
    today = datetime.now()
    end_date = today + timedelta(days=7)
    params = {
        "date": today.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    response = session.get(f"{API_BASE}/teams/{team_id}/activities", params=params)
    response.raise_for_status()
    return response.json()

def main():
    print("🔍 Tjekker Holdsport for aktiviteter...")

    teams = get_teams()
    for team in teams:
        activities = get_activities(team['id'])
        for activity in activities:
            if activity['name'].strip().lower() == ACTIVITY_NAME.strip().lower():
                print(f"✅ Fundet aktivitet: {activity['name']} på holdet {team['name']}")
                print(f"  ➤ Starttid: {activity.get('starttime', 'ukendt')}")
                print(f"  ➤ Lokation: {activity.get('place', 'ukendt')}")
                return

    print("❌ Ingen relevante aktiviteter fundet.")

if __name__ == "__main__":
    main()

