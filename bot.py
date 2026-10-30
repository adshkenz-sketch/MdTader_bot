import os
from flask import Flask
import threading
import telebot

# আপনার টেলিগ্রাম বট টোকেন
TOKEN = '9059878855:AAGQMCOK-2o9EMik1-ADrCoYxqJcU570-4M'
bot = telebot.TeleBot(TOKEN)

# রেন্ডার সার্ভার সচল রাখার জন্য ফ্লাস্ক (Flask) অ্যাপ
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "স্বাগত! আপনার মার্কেট অ্যানালাইসিস বট সফলভাবে চালু হয়েছে!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"আপনার বার্তা পেয়েছি: {message.text}")


if __name__ == '__main__':
    # ফ্লাস্ক সার্ভার ব্যাকগ্রাউন্ডে চালু করা
    t = threading.Thread(target=run_flask)
    t.start()
    
    print("Bot is running...")
    bot.infinity_polling()
