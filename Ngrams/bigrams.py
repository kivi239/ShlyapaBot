# coding=utf-8
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

def clear_word(word):
    letters = list(u".,…!?-()$#;:+=%^&*<>\"'[]{}\\/~—«»“„\n")
    for letter in letters:
        if word.find(letter) != -1:
            word = word.replace(letter, '')
    return word

next_words = dict()
prev_words = dict()

prev = ""
# need to find a good corpus for counting bi-grams
with open('file.txt') as f:
    for line in f:
        for word in line.split(" "):
            word = clear_word(word)
            if word not in next_words:
                next_words[word] = dict()
            if word not in prev_words:
                prev_words[word] = dict()

            if prev == "":
                prev = word
                continue

            if word not in next_words[prev]:
                next_words[prev][word] = 1
            else:
                next_words[prev][word] += 1

            if prev not in prev_words[word]:
                prev_words[word][prev] = 1
            else:
                prev_words[word][prev] = 1

            prev = word

print(prev_words)
print(next_words)


