import os
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

async def start(update, context):
    await update.message.reply_text("Botten kører!")

async def status(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Ikke autoriseret.")
        return
    await update.message.reply_text("Status OK!")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))

app.run_polling() 