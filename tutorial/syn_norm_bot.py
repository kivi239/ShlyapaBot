import config
import telebot
import pymorphy2
from string import whitespace

bot = telebot.TeleBot(config.token)
morph = pymorphy2.MorphAnalyzer()

syn_map = {}

def read_syn_dict(dictionary, divider = None):
    with open(dictionary) as f:
        for line in f.readlines():
            data = line.split(divider)[0]
            print(data)
            if data not in syn_map:
                syn_map[data] = set()
            for word in line.split(divider)[1:]:
                syn_map[data].add(word)


#read_syn_dict(config.syndict[0], "|")
read_syn_dict(config.syndict[1])

print("Dictionaries loaded")

def synnorm(word):
    norm = morph.parse(word)[0].normal_form
    if not norm in syn_map:
        return norm
    result = ""
    for word in syn_map[norm]:
        result += word + ", "
    return result[:-2]
    

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
            print(splitted_text)
            for text in splitted_text:
                bot.send_message(m.chat.id, text)

bot.polling()
