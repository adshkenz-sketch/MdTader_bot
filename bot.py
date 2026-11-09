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
    bot.reply_to(message, "Hello! Send '/best_signal' to get the best market signal.")

@bot.message_handler(commands=["best_signal", "signal"])
def get_best_market_signal(message):
    try:
        bot.reply_to(message, "⏳ রিয়েল ও ওটিসি মার্কেট স্ক্যান করা হচ্ছে...")

        # ১. রিয়েল এবং ওটিসি পেয়ারগুলোর কম্বাইন্ড লিস্ট
        pairs = [
            # রিয়েল ফরেক্স পেয়ার
            "EURUSD=X", "GBPUSD=X", "USDJPY=X",
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X",
            
            # ওটিসি (OTC) পেয়ার
            "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC",
            "AUDUSD-OTC", "USDCAD-OTC", "NZDUSD-OTC"
        ]

        best_pair = None
        max_change = -1
        best_price = 0
        best_signal_type = ""

        # সেরা মার্কেট খুঁজে বের করা
        for symbol in pairs:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m")
                
                if len(hist) >= 2:
                    latest_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    
                    price_change = abs(latest_price - previous_price) / previous_price
                    
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

        # ২. যদি ভালো পেয়ার পাওয়া যায়, আগে মার্কেটের নাম ও সিগন্যাল জানানো
        if best_pair:
            market_type = "OTC Market" if "-OTC" in best_pair else "Real Market"
            
            pre_notification = (
                f"🎯 **Best Market Found!**\n\n"
                f"• **Pair:** `{best_pair}`\n"
                f"• **Market Type:** {market_type}\n"
                f"• **Signal:** {best_signal_type}\n\n"
                f"⏳ রানিং ক্যান্ডেল শেষ হওয়ার জন্য অপেক্ষা করা হচ্ছে। ক্যান্ডেল ক্লোজ হওয়ামাত্র এন্ট্রি নেবেন!"
            )
            bot.reply_to(message, pre_notification, parse_mode="Markdown")

            # ৩. ক্যান্ডেল ক্লোজ হওয়া পর্যন্ত (পরবর্তী ক্যান্ডেলের শুরু পর্যন্ত) নিখুঁত অপেক্ষা
            now = datetime.now()
            next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
            sleep_seconds = (next_minute - now).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            # ৪. ঠিক ক্যান্ডেল ক্লোজ হওয়ার পর ফাইনাল এন্ট্রি অ্যালার্ট পাঠানো
            final_text = (
                f"🚀 **NOW ENTRY! (পরবর্তী ক্যান্ডেল শুরু হয়েছে)**\n\n"
                f"• **Pair:** `{best_pair}`\n"
                f"• **Rate:** `{best_price:.5f}`\n"
                f"• **Action:** {best_signal_type}\n\n"
                f"💡 **নির্দেশনা:** এখনই এই মার্কেটে পরবর্তী ক্যান্ডেলের জন্য ট্রেড প্লেস করুন!"
            )
            bot.send_message(message.chat.id, final_text, parse_mode="Markdown")
            
        else:
            bot.reply_to(message, "⚠️ এই মুহূর্তে কোনো মার্কেটে স্পষ্ট সিগন্যাল পাওয়া যায়নি। একটু পরে আবার চেষ্টা করুন।")

    except Exception as e:
        bot.reply_to(message, f"❌ এরর: সিগন্যাল জেনারেট করা যাচ্ছে না! ({str(e)})")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
                 
