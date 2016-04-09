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

with open('../synonymdict/all_from_easy.txt') as f:
    for line in f:
        data = line.split(" ")
        data = remove_empty_strings(data)
        count = int(data[1])
        word = clear_word(data[0])
        tags = morph.parse(word)[0].tag

        if 'NOUN' not in tags:
            continue

        word = morph.parse(word.rstrip())[0].normal_form
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

files = [None] * 4
files[0] = open('easy.txt', 'w', encoding="utf-8")
files[1] = open('normal.txt', 'w', encoding="utf-8")
files[2] = open('hard.txt', 'w', encoding="utf-8")
files[3] = open('nightmare.txt', 'w', encoding="utf-8") #, open('normal.txt', mode='w', decoding="utf-8"), open('hard.txt', mode='w', decoding="utf-8"), open('nightmare.txt', mode='w', deecoding="utf-8")]
all_words = open('all_levels.txt', mode='w', encoding="utf-8")

print(length)
id = -1
for i in reversed(range(length)):
    if sorted_words[i][1] != prev_freq and (length / 4) * (id + 1) <= (length - i - 1):
        id += 1
    prev_freq = sorted_words[i][1]
    print(id, length - i - 1, length)
    print(sorted_words[i][0])
    files[id].write(sorted_words[i][0] + ' ' + str(sorted_words[i][1]) + '\n')
    all_words.write(sorted_words[i][0] + ' ' + str(sorted_words[i][1]) + '\n')