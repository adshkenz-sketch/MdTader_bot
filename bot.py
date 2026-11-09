
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
    bot.reply_to(message, "হ্যালো! সবচেয়ে ভালো সিগন্যাল পেতে `/best_signal` বা `signal` কমান্ড পাঠান।")

# RSI হিসাব করার ফাংশন
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@bot.message_handler(commands=["best_signal", "signal"])
def get_best_market_signal(message):
    try:
        bot.reply_to(message, "🔍 রিয়াল মার্কেট স্ক্যান এবং ফিল্টারিং করা হচ্ছে...")

        # ১. নির্ভরযোগ্য মেজর পেয়ারগুলোর তালিকা (yfinance-এ OTC পেয়ারের সঠিক লাইভ ডেটা পাওয়া যায় না)
        pairs = [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X",
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X"
        ]

        best_pair = None
        max_strength = -1
        best_price = 0
        best_signal_type = ""

        # ২. প্রতিটি পেয়ারের ডেটা এনালাইসিস করা
        for symbol in pairs:
            try:
                ticker = yf.Ticker(symbol)
                # ১ মিনিটের ক্যান্ডেলের ডেটা নিয়ে কাজ করা
                hist = ticker.history(period="1d", interval="1m")
                
                if len(hist) >= 20:
                    # প্রাইস এবং ইনডিকেটর হিসাব
                    close_prices = hist['Close']
                    latest_price = close_prices.iloc[-1]
                    
                    # Moving Average (EMA 20) এবং RSI (14) হিসাব
                    ema_20 = close_prices.ewm(span=20, adjust=False).mean().iloc[-1]
                    rsi_series = calculate_rsi(close_prices, 14)
                    current_rsi = rsi_series.iloc[-1]
                    
                    # মোমেন্টাম বা শক্তির পরিমাপ
                    price_change = abs(latest_price - close_prices.iloc[-2])

                    # ৩. ফিল্টারিং লজিক (উইন রেট বাড়ানোর জন্য)
                    # যদি প্রাইস EMA-এর উপরে থাকে এবং RSI ওভারসোল্ড জোন থেকে ঘুরে আসে -> Call / UP
                    if latest_price > ema_20 and current_rsi > 45 and current_rsi < 70:
                        signal_type = "🟢 UP (Call - Bullish Trend)"
                        strength = price_change
                        
                        if strength > max_strength:
                            max_strength = strength
                            best_pair = symbol
                            best_price = latest_price
                            best_signal_type = signal_type

                    # যদি প্রাইস EMA-এর নিচে থাকে এবং RSI ওভারবট জোন থেকে নিচে নামে -> Put / Down
                    elif latest_price < ema_20 and current_rsi < 55 and current_rsi > 30:
                        signal_type = "🔴 DOWN (Put - Bearish Trend)"
                        strength = price_change
                        
                        if strength > max_strength:
                            max_strength = strength
                            best_pair = symbol
                            best_price = latest_price
                            best_signal_type = signal_type

            except Exception as ex:
                continue

        if best_pair:
            market_type = "Real Forex Market"
            
            pre_notification = (
                f"⭐ **Best Market Found!**\n\n"
                f"📊 **Pair:** `{best_pair}`\n"
                f"🌐 **Market Type:** `{market_type}`\n"
                f"📈 **Signal:** `{best_signal_type}`\n\n"
                f"⏳ ক্যান্ডেল ক্লোজ হওয়ার জন্য অপেক্ষা করা হচ্ছে। ক্যান্ডেল ক্লোজ হওয়া মাত্র এন্ট্রি নেবেন!"
            )
            bot.reply_to(message, pre_notification, parse_mode="Markdown")

            # ৮. ঠিক ক্যান্ডেল ক্লোজ হওয়ার পর ফাইনাল এন্ট্রি অ্যালার্ট পাঠানো
            now = datetime.now()
            next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
            sleep_seconds = (next_minute - now).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            final_text = (
                f"🚀 **NOW ENTRY! (পরবর্তী ক্যান্ডেল শুরু হয়েছে)**\n\n"
                f"📊 **Pair:** `{best_pair}`\n"
                f"💲 **Rate:** `{best_price:.5f}`\n\n"
                f"🎯 **Action:** `{best_signal_type}`\n"
                f"💡 **নির্দেশনা:** এখনই এই মার্কেটে পরবর্তী ক্যান্ডেলের জন্য ট্রেড প্লেস করুন!"
            )
            bot.send_message(message.chat.id, final_text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ এই মুহূর্তে মার্কেটে কোনো স্ট্রং ফিল্টারড সিগন্যাল পাওয়া যায়নি। একটু পরে আবার চেষ্টা করুন।")

    except Exception as e:
        bot.reply_to(message, f"❌ এরর: সিগন্যাল জেনারেট করা যাচ্ছে না! ({str(e)})")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)              
