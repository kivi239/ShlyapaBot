import config
import telebot
import random
import pymorphy2

class GameBot:
    """Shlyapa game bot"""
    def __init__(self):
        self.bot = telebot.TeleBot(config.token)
        self.morph = pymorphy2.MorphAnalyzer()

        self.syn_map = {}
        self.players = set()
        self.word_base = set()
        self.word_base_out = {}
        self.current_word = {}

        def read_word_base(dictionary, divider = None):
            with open(dictionary) as f:
                for line in f.readlines():
                    word = line.split(divider)[0]
                    if 'NOUN' in self.morph.parse(word)[0].tag:
                        self.word_base.add(word)

        def read_syn_dict(dictionary, divider = None):
            with open(dictionary) as f:
                for line in f.readlines():
                    data = line.split(divider)[0]
                    if data not in self.syn_map:
                        self.syn_map[data] = set()
                    for word in line.split(divider)[1:]:
                        self.syn_map[data].add(word)

        read_word_base(config.syndict[1])
#        read_syn_dict(config.syndict[0], "|")
        read_syn_dict(config.syndict[1])

        print("Dictionaries loaded")

    def synnorm(self, word):
        norm = self.morph.parse(word)[0].normal_form
        if not norm in self.syn_map:
            return norm
        result = ""
        for word in self.syn_map[norm]:
            result += word + ", "
        result.replace('\n','')
        return result[:-2]
        
    def new_word(self, player_id):
        word = random.choice(tuple(self.word_base ^ self.word_base_out[player_id]))
        print(word)
        return word

    def explain_synonyms(self, word):
        if not word in self.syn_map:
            return "Ой! Кажется, я загадал вам слово, объяснить которое не могу...\nСкоро это исправим. А пока нажмите сюда:/next"
        result = ""
        for wrd in self.syn_map[word]:
            result += wrd + ", "
        return result[:-2]

    def check_roots(self, word):
        return word

    def normal_form(self, word):
        norm = self.morph.parse(word)[0].normal_form
        return norm 

    def poll(self):
        @self.bot.message_handler(commands = ['start'])
        def greeter(m):
            player_id = m.chat.id
            print(player_id)
            self.bot.send_message(player_id, "Здравствуйте! Введите /next чтобы играть!")
            self.players.add(player_id)
            self.current_word[player_id] = "NOTAWORD"
            self.word_base_out[player_id] = set()

        @self.bot.message_handler(commands = ['help'])
        def helper(m):
            self.bot.send_message(m.chat.id, "Help:\n /next чтобы начать играть / пропустить слово.")

        @self.bot.message_handler(commands = ['next'])
        def starter(m):
            player_id = m.chat.id
            if not player_id in self.players:
                return

            if self.current_word[player_id] != "NOTAWORD":
                self.bot.send_message(player_id, "Вы не угадали слово %s" % (self.current_word[player_id]))
                self.word_base_out[player_id].add(self.current_word[player_id])
            self.current_word[player_id] = self.new_word(player_id)

            explanation = self.explain_synonyms(self.current_word[player_id])
            splitted_text = telebot.util.split_string(explanation, 3000)
            print(splitted_text)
            for text in splitted_text:
                self.bot.send_message(player_id, text)

        @self.bot.message_handler(func=lambda message: True)
        def listener(m):
            player_id = m.chat.id
            if not player_id in self.players:
                return
            if m.content_type == "text" and self.current_word[player_id] != "NOTAWORD":
                    if self.current_word[player_id] == self.normal_form(m.text):
                        self.bot.send_message(player_id, "Отлично! Сыграем снова: /next?")
                        self.current_word[player_id] = "NOTAWORD"
                    else:
                        response = ["Нет!", "Неправильно.", "Неа...", "Мимо", "Не то..."]
                        self.bot.send_message(player_id, random.choice(response))

        self.bot.polling()

hat = GameBot()
hat.poll()
