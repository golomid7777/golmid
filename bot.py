import json
import random
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

ADMIN_ID = 233804112
DATA_FILE = "participants.json"

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("ERROR: TOKEN environment variable is not set!")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def reg_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()
    user_id = str(user.id)
    if user_id in data:
        await update.message.reply_text("You are already registered!")
        return
    data[user_id] = {
        "name": user.full_name,
        "username": user.username or "user" + str(user.id),
        "paid": False
    }
    save_data(data)
    await update.message.reply_text("Registered successfully! Waiting for payment confirmation.")

async def list_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = load_data()
    if not data:
        await update.message.reply_text("No participants registered yet.")
        return
    text = "List of participants:\n\n"
    for uid, info in data.items():
        status = "paid" if info["paid"] else "not paid"
        username = info["username"]
        display_username = "@" + username if not username.startswith("user") else username        text += f"{info['name']} ({display_username}) - ID: {uid} - {status}\n"
    await update.message.reply_text(text)

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /pay <user_id>")
        return
    user_id = context.args[0]
    data = load_data()
    if user_id not in data:
        await update.message.reply_text("User with this ID not found.")
        return
    data[user_id]["paid"] = True
    save_data(data)
    username = data[user_id]["username"]
    display_username = "@" + username if not username.startswith("user") else username
    await update.message.reply_text(f"Payment confirmed for {display_username} (ID: {user_id})")

async def draw_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    count = 1
    if context.args:
        try:
            count = int(context.args[0])
            if count < 1:
                count = 1
        except ValueError:
            pass
    data = load_data()
    paid_users = [uid for uid, info in data.items() if info["paid"]]
    if not paid_users:
        await update.message.reply_text("No participants with confirmed payment.")
        return
    if count > len(paid_users):
        count = len(paid_users)
    winners = random.sample(paid_users, count)
    winner_names = []
    for wid in winners:
        info = data[wid]
        username = info["username"]
        display_username = "@" + username if not username.startswith("user") else username
        winner_names.append(f"{info['name']} ({display_username})")
    result = "\n".join(winner_names)
    await update.message.reply_text(f"Winners ({count}):\n\n{result}")

def main():
    app = Application.builder().token(TOKEN).build()    app.add_handler(CommandHandler("reg_user", reg_user))
    app.add_handler(CommandHandler("list", list_participants))
    app.add_handler(CommandHandler("pay", confirm_payment))
    app.add_handler(CommandHandler("win", draw_winners))
    print("Bot started!")
    app.run_polling()

if name == "main":
    main()