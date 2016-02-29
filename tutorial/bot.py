import config
import telebot

bot = telebot.TeleBot(config.token)

account=0

def add_answer(num):
    global account
    account += num

@bot.message_handler(commands = ['add'])
def answerer(m):
    num = int(m.text.split()[1]) if len(m.text.split()) > 1 else 0
    add_answer(num)

@bot.message_handler(commands = ['sub'])
def answerer(m):
    num = int(m.text.split()[1]) if len(m.text.split()) > 1 else 0
    add_answer(-num)

@bot.message_handler(commands = ['answer'])
def answerer(m):
    bot.send_message(m.chat.id, str(account))

@bot.message_handler(commands = ['start'])
def welcomer(m):
    bot.send_message(m.chat.id, "Welcome!")

@bot.message_handler(commands = ['help'])
def welcomer(m):
    bot.send_message(m.chat.id, "Help:\n /add N to add N\n /sub N to substract N \n /answer to get current result ")

@bot.message_handler(func=lambda message: True)
def listener(m):
    if m.content_type == "text":
        bot.send_message(m.chat.id, m.text)

bot.polling()
