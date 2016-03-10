import random
import telebot
import pymorphy2
from gensim.models import word2vec
import logging
import config

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

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

        logging.info("Dictionaries loaded")
        self.model = word2vec.Word2Vec.load_word2vec_format('/Volumes/TRANSCEND/models/ruscorpora.model.bin', binary=True)

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
        logging.info("Загадано слово %s" % word)
        return word

    def explain_synonyms(self, word):
        if not word in self.syn_map:
            return "Ой! Кажется, я загадал вам слово, объяснить которое не могу...\nСкоро это исправим. А пока нажмите сюда:/next"
        result = ""
        for wrd in self.syn_map[word]:
            if self.check_roots(wrd, word) != "NOTAWORD":
                result += wrd + ", "
        return "Синонимы к загаданному слову:\n" + result[:-2]

    def explain_closest_words(self, word):
        word_mod = word + '_S'
        if not word_mod in self.model.vocab:
            return "Ой! Кажется, я загадал вам слово, объяснить которое не могу...\nСкоро это исправим. А пока нажмите сюда:/next"
        result = ""
        for elem in self.model.most_similar(word_mod):
            wrd = elem[0][:-2]
            if self.check_roots(wrd, word) != "NOTAWORD":
                result += wrd + ", "
        return "Слова, употребляемые в сходном контексте с загаданным:\n" + result[:-2]

    def explain_main(self,word):
        return random.choice([self.explain_synonyms, self.explain_closest_words])(word)

    def check_roots(self, word, word2):
        return word

    def normal_form(self, word):
        norm = self.morph.parse(word)[0].normal_form
        return norm 

    def poll(self):
        @self.bot.message_handler(commands = ['start'])
        def greeter(m):
            player_id = m.chat.id
            self.bot.send_message(player_id, "Здравствуйте! Введите /next чтобы играть!\n Если застряли - жмите /help!")
            self.players.add(player_id)
            self.current_word[player_id] = "NOTAWORD"
            self.word_base_out[player_id] = set()

        @self.bot.message_handler(commands = ['help'])
        def helper(m):
            self.bot.send_message(m.chat.id, "Help:\n /next чтобы начать играть / пропустить слово. \n /repeat Чтобы впомнить объяснение/получить новое")

        @self.bot.message_handler(commands = ['next'])
        def starter(m):
            player_id = m.chat.id
            if not player_id in self.players:
                return

            if self.current_word[player_id] != "NOTAWORD":
                self.bot.send_message(player_id, "Вы не угадали слово %s" % (self.current_word[player_id]))
                self.word_base_out[player_id].add(self.current_word[player_id])
            self.current_word[player_id] = self.new_word(player_id)

            explanation = self.explain_main(self.current_word[player_id])
            logging.info(explanation)
            splitted_text = telebot.util.split_string(explanation, 3000)
            for text in splitted_text:
                self.bot.send_message(player_id, text)

        @self.bot.message_handler(commands = ['repeat'])
        def repeater(m):
            player_id = m.chat.id
            if not player_id in self.players:
                return
            if self.current_word[player_id] != "NOTAWORD":
                explanation = self.explain_main(self.current_word[player_id])
                logging.info(explanation)
                splitted_text = telebot.util.split_string(explanation, 3000)
                for text in splitted_text:
                    self.bot.send_message(player_id, text)

        @self.bot.message_handler(func=lambda message: True)
        def listener(m):
            player_id = m.chat.id
            if not player_id in self.players:
                return
            if m.content_type == "text" and self.current_word[player_id] != "NOTAWORD":
                    logging.info("Player %s tried word %s" % (str(m.chat.id), self.normal_form(m.text)))
                    if self.current_word[player_id] == self.normal_form(m.text):
                        self.bot.send_message(player_id, "Отлично! Сыграем снова: /next?")
                        self.current_word[player_id] = "NOTAWORD"
                    else:
                        response = ["Нет!", "Неправильно.", "Неа..."]
                        self.bot.send_message(player_id, random.choice(response))

        self.bot.polling()

hat = GameBot()
hat.poll()
