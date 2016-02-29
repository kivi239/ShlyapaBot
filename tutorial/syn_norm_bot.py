import config
import telebot
import pymorphy2

bot = telebot.TeleBot(config.token)
morph = pymorphy2.MorphAnalyzer()

syn_map = {}

with open(config.syndict) as f:
    for line in f.readlines():
        data = line.split("|")[0]
        if data not in syn_map:
            syn_map[data] = ""
        for word in line.split("|")[1:]:
            syn_map[data] += (", " + word) if syn_map[data] != "" else word

print("Dictionary loaded")

def synnorm(word):
    norm = morph.parse(word)[0].normal_form
    return syn_map[norm] if norm in syn_map else norm
    

@bot.message_handler(commands = ['start'])
def welcomer(m):
    bot.send_message(m.chat.id, "Welcome!")

@bot.message_handler(commands = ['help'])
def welcomer(m):
    bot.send_message(m.chat.id, "Help:\n Enter any word. Enjoy! ")

@bot.message_handler(func=lambda message: True)
def listener(m):
    if m.content_type == "text":
            splitted_text = telebot.util.split_string(synnorm(m.text), 3000)
            for text in splitted_text:
                bot.send_message(m.chat.id, text)

bot.polling()
