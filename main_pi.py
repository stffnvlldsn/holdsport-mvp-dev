import os
import requests
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import telegram
import asyncio
from telegram.ext import Application, CommandHandler, ContextTypes
import sys

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
ACTIVITY_NAME = os.getenv("HOLDSPORT_ACTIVITY_NAME", "Herre 4 træning").strip().lower()
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "7"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "180"))
STATUS_INTERVAL = int(os.getenv("STATUS_INTERVAL", "43200"))  # 12 hours in seconds

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "6052252183"))

# Global status tracking
status = {
    "start_time": datetime.now(),
    "last_check": None,
    "total_checks": 0,
    "successful_signups": 0,
    "last_error": None,
    "is_running": True,
    "restart": False
}

async def send_telegram_notification(message):
    """Send a notification via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("⚠️ Telegram credentials not configured", logging.WARNING)
        return
    
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        log_message("✅ Telegram notification sent successfully")
    except Exception as e:
        log_message(f"❌ Failed to send Telegram notification: {e}", logging.ERROR)

def log_message(message, level=logging.INFO):
    logging.log(level, message)

def generate_status_report():
    """Generate a detailed status report"""
    uptime = datetime.now() - status["start_time"]
    hours = uptime.total_seconds() / 3600
    
    report = f"""
📊 Holdsport Bot Status Report
⏱️ Uptime: {hours:.1f} hours
🔄 Total checks: {status["total_checks"]}
✅ Successful signups: {status["successful_signups"]}
⏰ Last check: {status["last_check"].strftime('%Y-%m-%d %H:%M:%S') if status["last_check"] else "Never"}
"""
    
    if status["last_error"]:
        report += f"❌ Last error: {status['last_error']}\n"
    
    return report

async def send_status_update():
    """Send periodic status updates"""
    while status["is_running"]:
        try:
            report = generate_status_report()
            await send_telegram_notification(report)
        except Exception as e:
            log_message(f"Error sending status update: {e}", logging.ERROR)
        await asyncio.sleep(STATUS_INTERVAL)

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

async def signup_for_activity(activity):
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
            success_message = f"🎉 Succes! Du er nu tilmeldt {activity.get('name', 'Herre 4 træning')}.\n" \
                            f"📅 Dato: {activity.get('starttime', 'Ukendt')}\n" \
                            f"📍 Lokation: {activity.get('place', 'Ukendt')}"
            log_message(success_message)
            await send_telegram_notification(success_message)
            status["successful_signups"] += 1
            return True
        else:
            error_msg = f"❌ Tilmelding fejlede – statuskode {response.status_code}"
            log_message(error_msg, logging.ERROR)
            status["last_error"] = error_msg
            return False
    except requests.RequestException as e:
        error_msg = f"[Fejl] Ved tilmelding: {e}"
        log_message(error_msg, logging.ERROR)
        status["last_error"] = error_msg
        return False

async def fetch_activities():
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

                if name != ACTIVITY_NAME:
                    continue

                log_message(f"✅ Fundet aktivitet: {activity['name']} på holdet {team_name}")
                log_message(f"  ➤ Starttid: {activity.get('starttime', 'Ukendt')}")
                log_message(f"  ➤ Lokation: {activity.get('place', 'Ukendt')}")

                status["last_check"] = datetime.now()
                status["total_checks"] += 1

                activity_status = str(activity.get("status", "")).lower()
                if activity_status == "tilmeldt":
                    log_message("ℹ️ Du er allerede tilmeldt.")
                    return
                else:
                    log_message("🟡 Forsøger at tilmelde dig...")
                    await signup_for_activity(activity)
                    return
    except requests.RequestException as e:
        error_msg = f"[Fejl] API-kald fejlede: {e}"
        log_message(error_msg, logging.ERROR)
        status["last_error"] = error_msg

# --- Telegram Command Handlers ---
async def status_command(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != TELEGRAM_ADMIN_ID:
        await update.message.reply_text("⛔️ You are not authorized to use this command.")
        return
    await update.message.reply_text(generate_status_report())

async def stop_command(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != TELEGRAM_ADMIN_ID:
        await update.message.reply_text("⛔️ You are not authorized to use this command.")
        return
    await update.message.reply_text("🛑 Stopping Holdsport Bot...")
    status["is_running"] = False

async def start_command(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != TELEGRAM_ADMIN_ID:
        await update.message.reply_text("⛔️ You are not authorized to use this command.")
        return
    await update.message.reply_text("🤖 Holdsport Bot is already running!")

async def restart_command(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != TELEGRAM_ADMIN_ID:
        await update.message.reply_text("⛔️ You are not authorized to use this command.")
        return
    await update.message.reply_text("🔄 Restarting Holdsport Bot...")
    status["restart"] = True
    status["is_running"] = False

async def telegram_command_listener():
    if not TELEGRAM_BOT_TOKEN:
        log_message("Telegram bot token not set, command listener not started.", logging.WARNING)
        return
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("restart", restart_command))
    log_message("🎧 Starter Telegram command listener")
    await application.run_polling()

async def main():
    log_message("🤖 Starter Holdsport-bot med tilmelding...")
    await send_telegram_notification("🚀 Holdsport Bot started on Raspberry Pi!")
    
    # Start status update task
    status_task = asyncio.create_task(send_status_update())
    telegram_task = asyncio.create_task(telegram_command_listener())
    
    try:
        while status["is_running"]:
            try:
                log_message("🔍 Tjekker Holdsport for aktiviteter...")
                await fetch_activities()
                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                error_msg = f"Uventet fejl: {e}"
                log_message(error_msg, logging.ERROR)
                status["last_error"] = error_msg
                await asyncio.sleep(60)  # Vent 1 minut ved uventede fejl
    except KeyboardInterrupt:
        status["is_running"] = False
        await send_telegram_notification("🛑 Holdsport Bot stopped!")
        log_message("Bot stopped by user")
    finally:
        status_task.cancel()
        telegram_task.cancel()
        try:
            await status_task
            await telegram_task
        except asyncio.CancelledError:
            pass
    # Handle restart
    if status.get("restart"):
        log_message("Restarting Holdsport Bot...")
        await send_telegram_notification("♻️ Holdsport Bot restarting now!")
        python = sys.executable
        os.execv(python, [python] + sys.argv)

if __name__ == "__main__":
    asyncio.run(main()) 