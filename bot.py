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
import yfinance as yf

# ইউএসডি মার্কেট সিগন্যাল কমান্ড
@bot.message_handler(commands=['usdsignal'])
def get_usd_signals(message):
    try:
        # উদাহরণস্বরূপ EUR/USD লাইভ ডেটা ফেচ
        ticker = yf.Ticker("EURUSD=X")
        df = ticker.history(period="1d", interval="1m")
        
        if df.empty:
            bot.reply_to(message, "⚠️ মার্কেট ডেটা পেতে সমস্যা হচ্ছে।")
            return
            
        latest_price = df['Close'].iloc[-1]
        previous_price = df['Close'].iloc[-2]
        
        # সহজ প্রাইস মোমেন্টাম চেক
        if latest_price > previous_price:
            signal = "📈 UP (Call)"
        else:
            signal = "📉 DOWN  (Put)  

try:
        response_text = (
            f"🔴 **USD Real Market Analysis**\n\n"
            f"• Pair: EUR/USD\n"
            f"• Current Rate: {latest_price:.5f}\n"
            f"• Signal: {signal}\n\n"
            f"⚠️ *সতর্কতা:* সিগন্যালটি নিশ্চিত করতে চার্ট অ্যানালিসিস মিলিয়ে নিন!"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"এরর: সিগন্যাল ফেচ করা যাচ্ছে না! ({str(e)})")

                 
