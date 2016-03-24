# coding=utf-8;

import random
import operator
import logging
import telebot
import pymorphy2
from gensim.models import word2vec
from numpy.random import choice
from nltk.stem.snowball import SnowballStemmer
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
        self.bigrams = {}
        self.probabilities = {}
        self.buttons = telebot.types.ReplyKeyboardMarkup()
        self.buttons.row("/repeat", "/next")
        self.level_buttons = telebot.types.ReplyKeyboardMarkup(row_width = 1)
        self.level_buttons.add("easy", "normal", "hard", "nightmare")
        self.level_pending = {}
        self.button_next = telebot.types.ReplyKeyboardMarkup()
        self.button_next.add("/next")
        self.buttons_hide = telebot.types.ReplyKeyboardHide()
        self.loggers = {}

        def read_word_base(dictionary, divider=None):
            with open(dictionary, encoding="utf-8") as fil:
                for line in fil.readlines():
                    word = line.split(divider)[0]
                    if 'NOUN' in self.morph.parse(word)[0].tag:
                        self.word_base.add(word)

        def read_syn_dict(dictionary, divider=None):
            with open(dictionary, encoding="utf-8") as fil:
                for line in fil.readlines():
                    data = line.split(divider)[0]
                    if data not in self.syn_map:
                        self.syn_map[data] = set()
                    for word in line.split(divider)[1:]:
                        self.syn_map[data].add(word)

        def read_bigrams(dictionary, order="reverse"):
            with open(dictionary) as fil:
                l_pr = 0
                r_pr = 0
                for line in fil.readlines():
                    if order == "reverse":
                        l_pr += 1
                        if l_pr % 5000 == 0:
                            logging.info(str(l_pr) + " reverse bigrams processed")
                        data = self.normal_form(line.split()[0])
                        adjs = line.split()[1:]
                        if data not in self.bigrams:
                            self.bigrams[data] = {}
                        for adj0, adj1 in zip(adjs[0::2], adjs[1::2]):
                            if adj0 not in self.bigrams[data]:
                                self.bigrams[data][adj0] = adj1
                            else:
                                self.bigrams[data][adj0] += adj1
                    if order == "direct":
                        r_pr += 1
                        if r_pr % 5000 == 0:
                            logging.info(str(r_pr) + " direct bigrams processed")
                        adj = line.split()[0]
                        nouns = line.split()[1:]
                        for noun0, noun1 in zip(nouns[0::2], nouns[1::2]):
                            snf = self.normal_form(noun0)
                            if snf not in self.bigrams:
                                self.bigrams[snf] = {}
                            if adj not in self.bigrams[snf]:
                                self.bigrams[snf][adj] = noun1
                            else:
                                self.bigrams[snf][adj] += noun1

        read_word_base(config.syndict[1])
#        read_syn_dict(config.syndict[0], "|")
        read_syn_dict(config.syndict[1])
#        read_bigrams(config.bigrams[1])
#        read_bigrams(config.bigrams[0], order="direct")
#        read_bigrams(config.bigrams[2], order="direct")
        read_bigrams(config.bigrams[3])



        logging.info("Dictionaries loaded")
        self.model = word2vec.Word2Vec.load_word2vec_format(config.corpuses[0], binary=True)

    def synnorm(self, word):
        norm = self.morph.parse(word)[0].normal_form
        if not norm in self.syn_map:
            return norm
        result = ""
        for word in self.syn_map[norm]:
            result += word + ", "
        result.replace('\n', '')
        return result[:-2]

    def new_word(self, player_id):
        word = random.choice(tuple(self.word_base ^ self.word_base_out[player_id]))
        logging.info("Загадано слово %s" % word)
        self.loggers[player_id].info("Загадано слово %s" % word)
        return word

    def explain_synonyms(self, word, player_id):
        self.probabilities[player_id] = [0, 0.6, 0.4]
        self.loggers[player_id].info("Объяснение синонимами")
        if not word in self.syn_map:
            return '''Ой! Кажется, я загадал вам слово, объяснить которое не могу...
Скоро это исправим. А пока нажмите на /next'''
        result = ""
        for wrd in self.syn_map[word]:
            if self.check_roots(wrd, word) != "NOTAWORD":
                result += wrd + ", "
        if result == "":
            return '''Ой! Кажется, я загадал вам слово, объяснить которое не могу...
Скоро это исправим. А пока нажмите сюда:/next'''
        return "Синонимы к загаданному слову:\n" + result[:-2]

    def explain_closest_words(self, word, player_id):
        self.probabilities[player_id] = [0.5, 0, 0.5]
        self.loggers[player_id].info("Объяснение контекстом")
        word_mod = word + '_S'
        if not word_mod in self.model.vocab:
            return '''Ой! Кажется, я загадал вам слово, объяснить которое не могу...
Скоро это исправим. А пока нажмите сюда:/next'''
        result = ""
        for elem in self.model.most_similar(word_mod):
            wrd = elem[0][:-2]
            if self.check_roots(wrd, word) != "NOTAWORD":
                result += wrd + ", "
        if result == "":
            return '''Ой! Кажется, я загадал вам слово, объяснить которое не могу...
Скоро это исправим. А пока нажмите сюда:/next'''
        return "Слова, употребляемые в сходном контексте с загаданным:\n" + result[:-2]

    def explain_bigrams(self, word, player_id):
        self.probabilities[player_id] = [0.4, 0.6, 0]
        self.loggers[player_id].info("Объяснение биграммами")
        if not word in self.bigrams:
            return "Ой! Кажется, с этим словом нет устойчивых выражений...\nНажмите сюда:/repeat"
        res = []
        adjs = self.bigrams[word]
        if len(adjs.keys()) > 3:
            sorted_adjs = sorted(adjs.items(), key=operator.itemgetter(1))
            res = [sorted_adjs[0][0], sorted_adjs[1][0], sorted_adjs[2][0]]
        else:
            res = adjs.keys()
        result = ""
        for word in res:
            result += word + " X\n"
        return "Выражения с загаданным словом:\n" + result[:-1]

    def explain_main(self, word, player_id):
        return choice([self.explain_synonyms, self.explain_closest_words, self.explain_bigrams],
                      p=self.probabilities[player_id])(word, player_id)

    def check_roots(self, word, word2):
        def cut_word(word):
            suffs = []
            res = [word]
            for suf in config.suffixes:
                if word.endswith(suf):
                    suffs.append(word[:-len(suf)])
                    res.append(word[:-len(suf)])
            for aff in config.affixes:
                for suf in suffs:
                    if suf.startswith(aff):
                        res.append(suf[len(aff):])
            return res

        stemmer = SnowballStemmer("russian")
        logging.info(word + " vs " +word2)
        if word in word2 or word2 in word:
            logging.info("One word contains another")
            return "NOTAWORD"
        word_ns = stemmer.stem(self.normal_form(word))
        word2_ns = stemmer.stem(self.normal_form(word2))
        logging.info(word_ns + " vs " +word2_ns)
        if word2_ns in word or word_ns in word2:
            logging.info("One word contains root of another")
            return "NOTAWORD"
        word_cs = cut_word(word_ns)
        word2_cs = cut_word(word2_ns)
        logging.info(' '.join(word_cs))
        logging.info(' '.join(word2_cs))
        if set(word_cs) & set(word2_cs):
            return "NOTAWORD"
        return word

    def normal_form(self, word):
        norm = self.morph.parse(word)[0].normal_form
        return norm

    def poll(self):
        @self.bot.message_handler(commands=['start'])
        def greeter(mess):
            player_id = mess.chat.id
            logging.info(str(player_id) + " started new game")
            self.level_pending[player_id] = True
            self.players.add(player_id)
            self.current_word[player_id] = "NOTAWORD"
            self.word_base_out[player_id] = set()
            self.loggers[player_id] = logging.getLogger(str(player_id))
            self.loggers[player_id].setLevel(logging.INFO)
            handler = logging.FileHandler(str(player_id) + ".log")
            self.loggers[player_id].addHandler(handler)
            self.loggers[player_id].info("Новая игра")
            self.bot.send_message(player_id, '''Здравствуйте! Выберите уровень сложности!
Нажмите /next чтобы выбрать другое слово!
Чтобы попросить другое объяснение, нажмите /repeat\n Помощь - введите /help!''',
                                  reply_markup=self.level_buttons)

            

        @self.bot.message_handler(commands=['help'])
        def helper(mess):
            player_id = mess.chat.id
            if not player_id in self.players:
                greeter(mess)
                return
            self.loggers[player_id].info("Просьба помощи")
            self.bot.send_message(mess.chat.id, '''Help:\n Нажмите next,
чтобы выбрать новое слово.
Нажмите repeat, чтобы получить новое объяснение''', reply_markup=self.buttons)

        @self.bot.message_handler(commands=['next'])
        def starter(mess):
            player_id = mess.chat.id
            self.probabilities[player_id] = [0.3, 0.5, 0.2]
            print("here")
            if not player_id in self.players:
                greeter(mess)
                return

            if self.current_word[player_id] != "NOTAWORD":
                self.loggers[player_id].info("Слово не угадано")
                self.bot.send_message(player_id, "Вы не угадали слово %s" %
                                      (self.current_word[player_id]),
                                      reply_markup=self.buttons)
                self.word_base_out[player_id].add(self.current_word[player_id])
            self.current_word[player_id] = self.new_word(player_id)

            explanation = self.explain_main(self.current_word[player_id], player_id)
            logging.info(explanation)
            splitted_text = telebot.util.split_string(explanation, 3000)
            for text in splitted_text:
                if len(text) > 2 and text[0] == 'О' and text[1] == 'й' and text[2] == '!':
                    self.bot.send_message(player_id, text, reply_markup=self.buttons)
                else:
                    self.bot.send_message(player_id, text)

        @self.bot.message_handler(commands=['repeat'])
        def repeater(mess):
            player_id = mess.chat.id
            if not player_id in self.players:
                greeter(mess)
                return
            if self.current_word[player_id] != "NOTAWORD":
                self.loggers[player_id].info("Повтор подсказки")
                explanation = self.explain_main(self.current_word[player_id], player_id)
                logging.info(explanation)
                splitted_text = telebot.util.split_string(explanation, 3000)
                for text in splitted_text:
                    if len(text) > 2 and text[0] == 'О' and text[1] == 'й' and text[2] == '!':
                        self.bot.send_message(player_id, text, reply_markup=self.buttons)
                    else:
                        self.bot.send_message(player_id, text)

        @self.bot.message_handler(func=lambda message: (message.text in config.levels.keys()))
        def leveller(mess):
            player_id = mess.chat.id
            if not player_id in self.players:
                greeter(mess)
                return
            self.loggers[player_id].info("Выбран уровень: %s" % mess.text)
            self.bot.send_message(player_id, config.level_responses[mess.text] + "\nНажмите /next, чтобы играть!",
                                  reply_markup=self.buttons)
            self.level_pending[player_id] = False

        @self.bot.message_handler(func=lambda message: True)
        def listener(mess):
            player_id = mess.chat.id
            if not player_id in self.players:
                greeter(mess)
                return
            if self.level_pending[player_id]:
                self.bot.send_message(player_id, config.level_responses["all"] + "\nНажмите /next, чтобы играть!",
                                      reply_markup=self.buttons)
                self.level_pending[player_id] = False
            if mess.content_type == "text" and self.current_word[player_id] != "NOTAWORD":
                logging.info("Player %s tried word %s" %
                             (str(mess.chat.id), self.normal_form(mess.text)))
                self.loggers[player_id].info("Попытка: %s" % self.normal_form(mess.text))
                if self.current_word[player_id] == self.normal_form(mess.text):
                    self.bot.send_message(player_id, "Отлично! Сыграем снова: /next?",
                                          reply_markup=self.buttons)
                    self.loggers[player_id].info("Слово угадано")
                    self.current_word[player_id] = "NOTAWORD"
                else:
                    response = ["Нет!", "Неправильно.", "Неа...", "Мимо", "Не то..."]
                    self.bot.send_message(player_id, random.choice(response))

        self.bot.polling()

HAT = GameBot()
HAT.poll()
