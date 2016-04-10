# encoding=utf-8

import pymorphy2
import operator

morph = pymorphy2.MorphAnalyzer()


def clear_word(word):
    letters = list("\n")
    for letter in letters:
        if word.find(letter) != -1:
            word = word.replace(letter, '')
    return word


def remove_empty_strings(data):
    new_data = []
    for word in data:
        if word != '':
            new_data.append(word)
    return new_data

freq_dict = dict()

with open('../synonymdict/1grams-3.txt', encoding='utf-8') as f:
    for line in f:
        line = line.rstrip("\n")
        data = line.split("\t")
        data = remove_empty_strings(data)

        print(data)
        count = int(data[0])
        word = clear_word(data[1])
        tags = morph.parse(word)[0].tag

        if 'NOUN' not in tags:
            continue

        word = morph.parse(word.rstrip())[0].normal_form
        if word == '':
            continue
        if word[0].isupper():
            continue
        if word not in freq_dict:
            freq_dict[word] = count
        else:
            freq_dict[word] += count

freq_dict = {k:v for k, v in freq_dict.items() if v > 1}

sorted_words = sorted(freq_dict.items(), key=operator.itemgetter(1))
length = len(sorted_words)

prev_freq = 1e9

path = '../synonymdict/levels/'

files = [open(path + 'easy.txt', mode='w', encoding="utf-8"), open(path + 'normal.txt', mode='w', encoding="utf-8"), open(path + 'hard.txt', mode='w', encoding="utf-8"), open(path + 'nightmare.txt', mode='w', encoding="utf-8")]
all_words = open(path + 'all_levels.txt', 'w', encoding="utf-8")

print(length)
id = -1
for i in reversed(range(length)):
    if sorted_words[i][1] != prev_freq and (length / 8) * (id + 1) <= (length - i - 1):
        id += 1
    if id > 3:
        id = 3
    prev_freq = sorted_words[i][1]
    print(id, length - i - 1, length)
    print(sorted_words[i][0])
    files[id].write(sorted_words[i][0] + ' ' + str(sorted_words[i][1]) + '\n')
    all_words.write(sorted_words[i][0] + ' ' + str(sorted_words[i][1]) + '\n')
