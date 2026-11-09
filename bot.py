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
    return "Smart Signal Bot is running successfully!"

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Hello! Send `/best_signal` to get the best market signal right now.")

# ব্যবহারকারী মেসেজ বা কমান্ড দিলে সেরা মার্কেট খুঁজে সিগন্যাল দেওয়ার হ্যান্ডলার
@bot.message_handler(commands=["best_signal", "signal"])
def get_best_market_signal(message):
    try:
        # আপনার পছন্দের মার্কেটগুলোর লিস্ট
        pairs = [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", 
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X"
        ]
        
        best_pair = None
        max_change = -1
        best_price = 0
        best_signal_type = ""
        
        # সব কটি মার্কেট চেক করে সবচেয়ে শক্তিশালী মুভমেন্ট বা ভালো মার্কেটটি খুঁজে বের করা
        for symbol in pairs:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="1m")
            
            if df.empty or len(df) < 2:
                continue
                
            latest_price = df["Close"].iloc[-1]
            previous_price = df["Close"].iloc[-2]
            
            # প্রাইসের পরিবর্তনের শতকরা হার (Percentage Change) হিসাব করা
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

        # যদি কোনো ভালো পেয়ার পাওয়া যায়
        if best_pair:
            response_text = (
                f"🎯 **Best Market Signal Found!**\n\n"
                f"• **Pair:** {best_pair}\n"
                f"  Current Rate: {best_price:.5f}\n"
                f"  Signal: {best_signal_type}\n\n"
                f"💡 *এই মুহূর্তে এই মার্কেটটিতে সবচেয়ে ভালো মুভমেন্ট পাওয়া গেছে।*"
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
                 
