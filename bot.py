import os
import threading
import telebot
from flask import Flask
import yfinance as yf

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
  raise ValueError("BOT_TOKEN is missing!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running successfully!"


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(message, "Hello! Bot is running successfully!")


# ইউএসডি মার্কেট সিগন্যাল কমান্ড
@bot.message_handler(commands=["usdsignal"])
def get_usd_signals(message):
try:
    # একাধিক মার্কেটের একটি লিস্ট তৈরি করুন (আপনার পছন্দমতো পেয়ার যোগ বা পরিবর্তন করতে পারেন)
    pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"]
    
    response_text = "📊 **Multi-Market Analysis**\n\n"
    
    for symbol in pairs:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval="1m")
        
        if df.empty:
            continue
            
        latest_price = df["Close"].iloc[-1]
        previous_price = df["Close"].iloc[-2]
        
        # সহজ প্রাইস মোমেন্টাম চেক
        if latest_price > previous_price:
            signal = "🟢 UP (Call)"
        else:
          signal = "🔴 DOWN (Put)"
            
        response_text += (
            f"• **Pair:** {symbol}\n"
            f"  Current Rate: {latest_price:.5f}\n"
            f"  Signal: {signal}\n\n"
        )
    
    response_text += "⚠️ **সতর্কতা:** সিগন্যালটি নিশ্চিত করতে চার্ট অ্যানালিসিস মিলিয়ে নিন।"
    bot.reply_to(message, response_text, parse_mode="Markdown")

except Exception as e:
    bot.reply_to(message, f"❌ এরর: সিগন্যাল ফেচ করা যাচ্ছে না! ({str(e)})")

# এর পরের বটের রান ও ফ্লাস সার্ভারের অংশ অপরিবর্তিত থাকবে
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে টেলিগ্রাম বট চালু করার জন্য থ্রেড রান করা
    t = threading.Thread(target=run_bot)
    t.start()

    # ওয়েব সার্ভারের জন্য পোর্ট বাইন্ড করা
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
                 
