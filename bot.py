 import os
import threading
import time
from datetime import datetime, timedelta
from flask import Flask
import yfinance as yf
import telebot
import numpy as np
import pandas as pd

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
    bot.reply_to(message, "হ্যালো! সবচেয়ে ভালো সিগন্যাল পেতে '/best_signal' বা 'signal' কমান্ড পাঠান।")

# ইনডিকেটর এবং সাপোর্ট/রেজিস্ট্যান্স ক্যালকুলেশন ফাংশন
def calculate_indicators(df, window=20):
    # ১. Exponential Moving Average (EMA)
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()

    # ২. Relative Strength Index (RSI - 14 period)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # ৩. Average True Range (ATR - 14 period) - ভোলাটিলিটি ফিল্টার
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(window=14).mean()
    df['ATR_Avg'] = df['ATR'].rolling(window=50).mean()

    # ৪. Dynamic Support & Resistance Levels
    df['Resistance'] = df['high'].rolling(window=window).max()
    df['Support'] = df['low'].rolling(window=window).min()

    return df

@bot.message_handler(commands=["best_signal", "signal"])
def get_best_market_signal(message):
    try:
        bot.reply_to(message, "🔍 রিয়াল মার্কেট স্ক্যান এবং ফিল্টারিং করা হচ্ছে...")
        
        pairs = [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", 
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X"
        ]
        
        best_pair = None
        max_strength = -1
        best_price = 0
        best_signal_type = ""
        
        for symbol in pairs:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m")
                
                if len(hist) >= 50:
                    # yfinance কলামের নামগুলো ক্যাপিটাল হতে পারে, তাই লোয়ারকেস করে নেওয়া ভালো
                    hist = hist.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
                    
                    # ইন্ডিকেটর ক্যালকুলেট করা
                    df = calculate_indicators(hist)
                    latest = df.iloc[-1]
                    
                    close_price = latest['close']
                    ema_50 = latest['EMA_50']
                    ema_200 = latest['EMA_200']
                    rsi = latest['RSI']
                    atr = latest['ATR']
                    atr_avg = latest['ATR_Avg']
                    resistance = latest['Resistance']
                    support = latest['Support']
                    
                    # ভোলাটিলিটি চেক (সাইডওয়েজ মার্কেট এড়াতে)
                    if atr < (atr_avg * 0.7):
                        continue
                        
                    price_change = abs(close_price - df.iloc[-2]['close'])
                    
                    # সাপোর্ট ও রেজিস্ট্যান্সের দূরত্ব চেক (যেমন: ০.১৫% এর মধ্যে)
                    is_near_support = abs(close_price - support) / support <= 0.0015
                    is_near_resistance = abs(close_price - resistance) / resistance <= 0.0015
                    
                    signal_type = ""
                    # CALL / BUY সিগন্যাল লজিক
                    if (close_price > ema_50) and (ema_50 > ema_200) and (40 < rsi < 65) and is_near_support:
                        signal_type = "🟢 CALL (Buy - Uptrend at Support)"
                    
                    # PUT / SELL সিগন্যাল লজিক
                    elif (close_price < ema_50) and (ema_50 < ema_200) and (35 < rsi < 60) and is_near_resistance:
                        signal_type = "🔴 PUT (Sell - Downtrend at Resistance)"
                        
                    if signal_type and price_change > max_strength:
                        max_strength = price_change
                        best_pair = symbol
                        best_price = close_price
                        best_signal_type = signal_type
                        
            except Exception as e:
                continue
                
        if best_pair:
            market_type = "Real Forex Market"
            pre_notification = (
                f"⭐ **Best Market Found!**\n\n"
                f"📌 **Pair:** `{best_pair}`\n"
                f"📊 **Market Type:** `{market_type}`\n"
                f"🎯 **Signal:** `{best_signal_type}`\n"
                f"⏳ ক্যান্ডেল ক্লোজ হওয়ার জন্য অপেক্ষা করা হচ্ছে। ক্যান্ডেল ক্লোজ হওয়া মাত্র এন্ট্রি নেবেন!"
            )
            bot.reply_to(message, pre_notification, parse_mode="Markdown")
            
            # ঠিক ক্যান্ডেল ক্লোজ হওয়ার পর ফাইনাল এন্ট্রি অ্যালার্ট পাঠানো
            now = datetime.now()
            next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
            sleep_seconds = (next_minute - now).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
                
            final_text = (
                f"🚀 **NOW ENTRY! (পরবর্তী ক্যান্ডেল শুরু হয়েছে)**\n\n"
                f"📌 **Pair:** `{best_pair}`\n"
                f"💲 **Rate:** `{best_price:.5f}`\n"
                f"⚡ **Action:** `{best_signal_type}`\n"
                f"🎯 **নির্দেশনা:** এখন এই মার্কেটে পরবর্তী ক্যান্ডেলের জন্য ট্রেড প্লেস করুন!"
            )
            bot.send_message(message.chat.id, final_text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ এই মুহূর্তে মার্কেটে কোনো শক্তিশালী সাপোর্ট/রেজিস্ট্যান্স ও ট্রেন্ড ফিল্টারে সিগন্যাল পাওয়া যায়নি। একটু পরে আবার চেষ্টা করুন।")
            
    except Exception as e:
        bot.reply_to(message, f"❌ এরর: সিগন্যাল জেনারেট করা যাচ্ছে না! ({str(e)})")
def run_bot():
    time.sleep(3)  # সার্ভার স্টার্ট হওয়ার পর ৩ সেকেন্ড অপেক্ষা করবে
    try:
        bot.remove_webhook(remove_pending_updates=True)  # আগের সব পেন্ডিং আপডেট ও ওয়েভহুক ক্লিয়ার করবে
        time.sleep(2)
    except Exception as e:
        print(f"Webhook error: {e}")
    
    bot.infinity_polling(none_stop=True, interval=1, timeout=20)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



