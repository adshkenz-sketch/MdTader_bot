import telebot

TOKEN = '9059878855:AAGQMCOk-2o9EMik1-ADrCoYxqJcU570-4M'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(message, 'Hello! Bot is running successfully!')


bot.infinity_polling()
