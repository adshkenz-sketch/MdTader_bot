import telebot
TOKEN = '9068473030:AAEJ1vX49_x7Ufwffz6VyTK5pT3RDStaeqY'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Hello! Bot is running successfully!')

bot.infinity_polling()
