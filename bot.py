import os
import threading
import telebot
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running successfully!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Hello! Bot is running successfully!')

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে টেলিগ্রাম বট চালু করার জন্য থ্রেড রান করা
    t = threading.Thread(target=run_bot)
    t.start()
    
    # রেন্ডার সার্ভারের জন্য পোর্ট বাইন্ড করা
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
