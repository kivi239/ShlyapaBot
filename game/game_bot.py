# coding=utf-8;

import random
import operator
import logging
import collections
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
        self.word_base = {}
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
        self.scores = collections.defaultdict(int)
        self.levels = {}
        self.names = {}

        def read_word_base(dictionary, divider=None):
            wb = set()
            with open(dictionary, encoding='utf-8') as fil:
                for line in fil.readlines():
                    word = line.split(divider)[0]
                    if 'NOUN' in self.morph.parse(word)[0].tag:
                        wb.add(word)
            return wb

        def read_syn_dict(dictionary, divider=None):
            with open(dictionary, encoding="utf-8") as fil:
                l_pr = 0
                for line in fil.readlines():
                    l_pr += 1
                    if l_pr % 1000 == 0:
                        logging.info(str(l_pr) + " reverse bigrams processed")
                    data = line.split(divider)[0]
                    if data not in self.syn_map:
                        self.syn_map[data] = set()
                    for word in line.split(divider)[1:]:
                        self.syn_map[data].add(word)

        def read_bigrams(dictionary, order="reverse"):
            with open(dictionary, encoding='utf-8') as fil:
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
                            self.bigrams[data] = collections.defaultdict(int);
                        for adj0, adj1 in zip(adjs[0::2], adjs[1::2]):
                            try:
                                self.bigrams[data][adj0] += int(adj1)
                            except ValueError:
                                self.bigrams[data][adj0] += 0
                    if order == "direct":
                        r_pr += 1
                        if r_pr % 5000 == 0:
                            logging.info(str(r_pr) + " direct bigrams processed")
                        adj = line.split()[0]
                        nouns = line.split()[1:]
                        for noun0, noun1 in zip(nouns[0::2], nouns[1::2]):
                            snf = self.normal_form(noun0)
                            if snf not in self.bigrams:
                                self.bigrams[snf] = collections.defaultdict(int)
                            try:
                                self.bigrams[snf][adj] += int(noun1)
                            except ValueError:
                                self.bigrams[snf][adj] += 0

        def read_score_table(table):
            with open(table, encoding='utf-8') as fil:
                for line in fil.readlines():
                    self.scores[" ".join(line.split()[:-1])] = int(line.split()[-1])
                        
        for level in config.levels:
            self.word_base[level] = read_word_base(config.levels[level])
        read_syn_dict(config.syndict[1])
        read_bigrams(config.bigrams[3])
        read_bigrams(config.bigrams[4])
        read_score_table(config.score_table)

        logging.info("Dictionaries loaded")
        self.model = word2vec.Word2Vec.load_word2vec_format(config.corpuses[0], binary=True)

    def similar_words(self, word1, word2):
        n = len(word1)
        m = len(word2)
        d = [None] * (n + 1)
        for i in range(n + 1):
            d[i] = []
            for j in range(m + 1):
                d[i].append(int(1e9))
        for i in range(n):
            d[i + 1][0] = i
        for i in range(m):
            d[0][i + 1] = i
        d[0][0] = 0

        for i in range(n):
            for j in range(m):
                d[i + 1][j + 1] = min(d[i + 1][j + 1], d[i][j + 1] + 1, d[i + 1][j] + 1)
                diff = 1
                if word1[i] == word2[j]:
                    diff = 0
                d[i + 1][j + 1] = min(d[i + 1][j + 1], d[i][j] + diff)

        return d[n][m] <= 2

    def synnorm(self, word):
        norm = self.morph.parse(word)[0].normal_form
        if norm not in self.syn_map:
            return norm
        result = ""
        for word in self.syn_map[norm]:
            result += word + ", "
        result.replace('\n', '')
        return result[:-2]

    def new_word(self, player_id):
        word = random.choice(tuple(self.word_base[self.levels[player_id]] ^ self.word_base_out[player_id]))
        logging.info("Загадано слово %s" % word)
        self.loggers[player_id].info("Загадано слово %s" % word)
        return word

    def explain_synonyms(self, word, player_id):
        self.probabilities[player_id][0] = 0
        self.loggers[player_id].info("Объяснение синонимами")
        if word not in self.syn_map:
            return config.NOTAWORD
        result = ""
        for wrd in self.syn_map[word]:
            if self.check_roots(wrd, word) != config.NOTAWORD:
                result += wrd + ", "
        if result == "":
            return config.NOTAWORD
        return "Синонимы к загаданному слову:\n" + result[:-2]

    def explain_closest_words(self, word, player_id):
        self.probabilities[player_id][1] = 0
        self.loggers[player_id].info("Объяснение контекстом")
        word_mod = word + '_S'
        if word_mod not in self.model.vocab:
            return config.NOTAWORD
        result = ""
        for elem in self.model.most_similar(word_mod):
            wrd = elem[0].split('_')[0]
            if self.check_roots(wrd, word) != config.NOTAWORD:
                result += wrd + ", "
        if result == "":
            return config.NOTAWORD
        return "Слова, употребляемые в сходном контексте с загаданным:\n" + result[:-2]

    def explain_bigrams(self, word, player_id):
        self.probabilities[player_id][2] = 0
        self.loggers[player_id].info("Объяснение биграммами")
        if word not in self.bigrams:
            return config.NOTAWORD
        res = []
        adjs = self.bigrams[word]
        if len(adjs.keys()) > 3:
            print(adjs)
            sorted_adjs = [x[0] for x in sorted(adjs.items(), key=operator.itemgetter(1), reverse=True)]
            if self.check_roots(sorted_adjs[0], word) != config.NOTAWORD:
                res = [sorted_adjs[0]]
            
            for wrd in sorted_adjs:
                if len(res) >= 3:
                    break
                if self.normal_form(wrd) not in [self.normal_form(x) for x in res] and \
                   self.check_roots(wrd, word) != config.NOTAWORD:
                    res.append(wrd)
        else:
            res = adjs.keys()
        result = ""
        for word in res:
            result += word + " X\n"
        return "Выражения с загаданным словом:\n" + result[:-1]

    def explain_main(self, word, player_id):
        if sum(self.probabilities[player_id]) == 0:
            self.probabilities[player_id] = [0.3, 0.5, 0.2]
        explanation = config.NOTAWORD
        while explanation == config.NOTAWORD and sum(self.probabilities[player_id]) != 0:
            sump = sum(self.probabilities[player_id])
            if sump != 1:
                for i, prob in enumerate(self.probabilities[player_id]):
                    if prob != 0:
                        self.probabilities[player_id][i] += (1 - sump)
                        break
            explanation = choice([self.explain_synonyms, self.explain_closest_words, self.explain_bigrams],
                      p=self.probabilities[player_id])(word, player_id)
        if explanation == config.NOTAWORD:
            if set(self.probabilities[player_id]) == set([0.3, 0.5, 0.2]):
                return '''Ой! Кажется, я загадал вам слово, объяснить которое не могу...
Скоро это исправим. А пока нажмите сюда:/next'''
            else:
                explanation = self.explain_main(word, player_id)
        return explanation

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

        def cut_deep(word):
            res_start = cut_word(word)
            res = []
            for wrd in res_start:
                res = res + cut_word(wrd)
                return res

        stemmer = SnowballStemmer("russian")
        logging.info(word + " vs " +word2)
        if word in word2 or word2 in word:
            logging.info("One word contains another")
            return config.NOTAWORD
        word_ns = stemmer.stem(self.normal_form(word))
        word2_ns = stemmer.stem(self.normal_form(word2))
        logging.info(word_ns + " vs " + word2_ns)
        if word2_ns in word or word_ns in word2:
            logging.info("One word contains root of another")
            return config.NOTAWORD
        word_cs = cut_deep(word_ns)
        word2_cs = cut_deep(word2_ns)
        logging.info(' '.join(word_cs))
        logging.info(' '.join(word2_cs))
        if set(word_cs) & set(word2_cs):
            return config.NOTAWORD
        return word

    def normal_form(self, word):
        norm = self.morph.parse(word)[0].normal_form
        return norm

    def save_scores(self, table = config.score_table):
        with open(table, 'r+') as fil:
            for person in self.scores:
                fil.write(person + " " + str(self.scores[person]) + "\n")
        

    def poll(self):
        @self.bot.message_handler(commands=['start'])
        def greeter(mess):
            player_id = mess.chat.id
            if mess.chat.type == "private":
                self.names[player_id] = mess.from_user.first_name 
                if mess.from_user.last_name is not None:
                    self.names[player_id] += " " +  mess.from_user.last_name
            else:
                self.names[player_id] = mess.chat.title 

            logging.info(str(player_id) + " started new game")
            self.level_pending[player_id] = True
            self.players.add(player_id)
            self.current_word[player_id] = config.NOTAWORD
            self.word_base_out[player_id] = set()
            self.loggers[player_id] = logging.getLogger(str(player_id))
            self.loggers[player_id].setLevel(logging.INFO)
            handler = logging.FileHandler("log" + str(player_id) + ".log")
            self.loggers[player_id].addHandler(handler)
            self.loggers[player_id].info("Новая игра")
            self.bot.send_message(player_id, '''Здравствуйте! Выберите уровень сложности!
Нажмите /next чтобы выбрать другое слово!
Чтобы попросить другое объяснение, нажмите /repeat\n Помощь - введите /help!''',
                                  reply_markup=self.level_buttons)

        @self.bot.message_handler(commands=['help'])
        def helper(mess):
            player_id = mess.chat.id
            if player_id not in self.players:
                greeter(mess)
                return
            self.loggers[player_id].info("Просьба помощи")
            self.bot.send_message(mess.chat.id, '''Help:\n Нажмите next,
чтобы выбрать новое слово.
Нажмите repeat, чтобы получить новое объяснение''', reply_markup=self.buttons)

        @self.bot.message_handler(commands=['score'])
        def scorer(mess):
            player_id = mess.chat.id
            if player_id not in self.players:
                greeter(mess)
            res = ""
            player_name = self.names[player_id]
            for n, person in enumerate(sorted(self.scores.items(), key = operator.itemgetter(1), reverse = True)):
                if person[0] == player_name:
                    res += "*" + str(n) + ".) " + self.names[player_id] + " " + str(person[1]) + "*\n"
                else:
                    res += str(n) + ".) " + person[0] + " " + str(person[1]) + "\n"
            self.bot.send_message(player_id, res, parse_mode = "Markdown")

        @self.bot.message_handler(commands=['next'])
        def starter(mess):
            player_id = mess.chat.id
            self.probabilities[player_id] = [0.3, 0.5, 0.2]
            print("here")
            if player_id not in self.players or player_id not in self.levels:
                greeter(mess)
                return

            if self.current_word[player_id] != config.NOTAWORD:
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
            if player_id not in self.players:
                greeter(mess)
                return
            if self.current_word[player_id] != config.NOTAWORD:
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
            if player_id not in self.players:
                greeter(mess)
                return
            self.loggers[player_id].info("Выбран уровень: %s" % mess.text)
            self.bot.send_message(player_id, config.level_responses[mess.text] + "\nНажмите /next, чтобы играть!",
                                  reply_markup=self.buttons)
            self.levels[player_id] = mess.text
            self.level_pending[player_id] = False

        @self.bot.message_handler(func=lambda message: (message.text.startswith("Загадай")))
        def secret(mess):
            player_id = mess.chat.id
            if not player_id in self.players:
                self.bot.send_message(player_id, "Секретное меню - только для залогиненных пользователей, нажмите /start")
                return
            word = mess.text.split()[1]
            for expl in [self.explain_synonyms, self.explain_closest_words, self.explain_bigrams]:
                explanation = expl(word, player_id)
                logging.info(explanation)
                splitted_text = telebot.util.split_string(explanation, 3000)
                for text in splitted_text:
                    if len(text) > 2 and text[0] == 'О' and text[1] == 'й' and text[2] == '!':
                        self.bot.send_message(player_id, text, reply_markup=self.buttons)
                    else:
                        self.bot.send_message(player_id, text)

        @self.bot.message_handler(func=lambda message: True)
        def listener(mess):
            player_id = mess.chat.id
            if not player_id in self.players:
                greeter(mess)
                return
            if self.level_pending[player_id]:
                self.bot.send_message(player_id, config.level_responses["all"] + "\nНажмите /next, чтобы играть!",
                                      reply_markup=self.buttons)
                self.levels[player_id] = "all"
                self.level_pending[player_id] = False
            if mess.content_type == "text" and self.current_word[player_id] != config.NOTAWORD:
                logging.info("Player %s tried word %s" %
                             (str(mess.chat.id), self.normal_form(mess.text)))
                self.loggers[player_id].info("Попытка: %s" % self.normal_form(mess.text))
                if self.similar_words(self.current_word[player_id], self.normal_form(mess.text)):
                    self.bot.send_message(player_id, "Отлично! Вы отгадали слово %s.\n Сыграем снова: /next?"
                                          % self.current_word[player_id],
                                          reply_markup=self.buttons)
                    self.loggers[player_id].info("Слово угадано")
                    self.scores[self.names[player_id]] += 1
                    self.current_word[player_id] = config.NOTAWORD
                else:
                    response = ["Нет!", "Неправильно.", "Неа...", "Мимо", "Не то..."]
                    self.bot.send_message(player_id, random.choice(response))

        self.bot.polling()

HAT = GameBot()
try:
    HAT.poll()
finally:
    HAT.save_scores()
