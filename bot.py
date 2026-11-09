import os
import threading
import time
from datetime import datetime, timedelta
from flask import Flask
import yfinance as yf
import telebot

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Smart Signal Bot is running successfully!"

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Hello! Send '/best_signal' to get the best market signal for the next candle.")

# ব্যবহারকারী মেসেজ বা কমান্ড দিলে সেরা মার্কেট খুঁজে পরবর্তী ক্যান্ডেলের সিগন্যাল দেওয়ার হ্যান্ডলার
@bot.message_handler(commands=["best_signal", "signal"])
def get_best_market_signal(message):
    try:
        bot.reply_to(message, "⏳ পরবর্তী ক্যান্ডেল শুরু হওয়া পর্যন্ত অপেক্ষা করা হচ্ছে এবং রিয়েল ও ওটিসি মার্কেট স্ক্যান করা হচ্ছে...")
        
        # বর্তমান ক্যান্ডেল ক্লোজ হওয়া পর্যন্ত (পরবর্তী ক্যান্ডেলের শুরু পর্যন্ত) নিখুঁত অপেক্ষা
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        sleep_seconds = (next_minute - now).total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

        # ১. আপনার পছন্দের রিয়েল এবং ওটিসি পেয়ারগুলোর কম্বাইন্ড লিস্ট
        pairs = [
            # রিয়েল ফরেক্স পেয়ার
            "EURUSD=X", "GBPUSD=X", "USDJPY=X",
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X",
            
            # ওটিসি (OTC) পেয়ার (আপনার প্ল্যাটফর্ম অনুযায়ী)
            "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC",
            "AUDUSD-OTC", "USDCAD-OTC", "NZDUSD-OTC"
        ]

        best_pair = None
        max_change = -1
        best_price = 0
        best_signal_type = ""

        # সব কটি মার্কেট চেক করে সবচেয়ে শক্তিশালী মুভমেন্ট বা ভালো মার্কেটটি খুঁজে বের করা
        for symbol in pairs:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m")
                
                if len(hist) >= 2:
                    latest_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    
                    # প্রাইসের পরিবর্তন বা ভোলাটিলিটি বের করা
                    price_change = abs(latest_price - previous_price) / previous_price
                    
                    # যে মার্কেটে মুভমেন্ট বা পরিবর্তন সবচেয়ে বেশি পাওয়া যাবে, সেটি সিলেক্ট হবে
                    if price_change > max_change:
                        max_change = price_change
                        best_pair = symbol
                        best_price = latest_price
                        if latest_price > previous_price:
                            best_signal_type = "🟢 UP (Call - Strong Bullish)"
                        else:
                            best_signal_type = "🔴 DOWN (Put - Strong Bearish)"
            except Exception as ex:
                print(f"Error fetching {symbol}: {ex}")
                continue

        # যদি কোনো ভালো পেয়ার পাওয়া যায়
        if best_pair:
            market_type = "OTC Market" if "-OTC" in best_pair else "Real Market"
            response_text = (
                f"🎯 **Next Candle Signal Found!**\n\n"
                f"• **Pair:** `{best_pair}`\n"
                f"• **Market Type:** {market_type}\n"
                f"• **Current Rate:** `{best_price:.5f}`\n"
                f"• **Signal:** {best_signal_type}\n\n"
                f"💡 **নির্দেশনা:** রানিং ক্যান্ডেল বাদ দেওয়া হয়েছে। **পরবর্তী ক্যান্ডেলের শুরুতে (00 সেকেন্ডে)** ট্রেড প্লেস করুন!"
            )
        else:
            response_text = "⚠️ এই মুহূর্তে কোনো মার্কেটে স্পষ্ট সিগন্যাল পাওয়া যায়নি। একটু পরে আবার চেষ্টা করুন।"

        bot.reply_to(message, response_text, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ এরর: সিগন্যাল জেনারেট করা যাচ্ছে না! ({str(e)})")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে টেলিগ্রাম বট চালু করার জন্য থ্রেড রান করা
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    # ওয়েব সার্ভারের জন্য পোর্ট বাইন্ড করা
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
                 
