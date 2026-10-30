import os
import telebot

# আপনার টেলিগ্রাম বট টোকেন
TOKEN = '9059878855:AAGQMCOK-2o9EMik1-ADrCoYxqJcU570-4M'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "স্বাগতম! আপনার মার্কেট অ্যানালাইসিস বট সফলভাবে চালু হয়েছে।")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"আপনার বার্তা পেয়েছি: {message.text}")

# বটের রান করার ব্যবস্থা
if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
