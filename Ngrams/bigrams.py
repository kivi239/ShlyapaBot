#coding=utf-8
import pymorphy2
import operator

def clear_word(word):
    letters = list("\n.,!?P()[]{}'\"")
    for letter in letters:
        if word.find(letter) != -1:
            word = word.replace(letter, '')
    return word

next_words = dict()
prev_words = dict()

morph = pymorphy2.MorphAnalyzer()

prev = ""
# need to find a good corpus for counting bi-grams
with open('ansi.txt') as f:
    for line in f:
        for word in line.split(" "):
            word = clear_word(word)
            tags = morph.parse(word)[0].tag
            prev_tags = morph.parse(prev)[0].tag
            if 'NOUN' not in tags and 'ADJF' not in tags:
                continue

            if word not in next_words and 'ADJF' in tags:
                next_words[word] = dict()
            if word not in prev_words and 'NOUN' in tags:
                prev_words[word] = dict()

            if prev == "":
                prev = word
                continue

            if 'ADJF' in prev_tags and 'NOUN' in tags:
                if word not in next_words[prev]:
                    next_words[prev][word] = 1
                else:
                    next_words[prev][word] += 1

                if prev not in prev_words[word]:
                    prev_words[word][prev] = 1
                else:
                    prev_words[word][prev] += 1

            prev = word

#print(prev_words)
#print(next_words)

output = open('bigrams_next.txt', 'w')
for key in next_words.keys():
    sorted_next = sorted(next_words[key].items(), key=operator.itemgetter(1))
    if len(sorted_next) == 0:
        continue

    output.write(key + ' ')
    for i in range(min(10, len(sorted_next))):
        output.write(sorted_next[i][0] + ' ')
        output.write(str(sorted_next[i][1]))
        output.write(' ')
    output.write('\n')

output2 = open('bigrams_prev.txt', 'w')
for key in prev_words.keys():
    sorted_prev = sorted(prev_words[key].items(), key=operator.itemgetter(1))
    if len(sorted_prev) == 0:
        continue

    output2.write(key + ' ')
    for i in range(min(10, len(sorted_prev))):
        output2.write(sorted_prev[i][0] + ' ')
        output2.write(str(sorted_prev[i][1]))
        output2.write(' ')
    output2.write('\n')