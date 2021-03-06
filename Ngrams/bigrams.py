#coding=utf-8
import operator

B = 500000  # Number of line to be processed before pushing the results in output file

def clear_word(word):
    letters = list("\n.,!?P()[]{}`'\"/~—«»:")
    for letter in letters:
        if word.find(letter) != -1:
            word = word.replace(letter, '')
    return word


def is_word(word):
    for c in word:
        if c.isalpha():
            return True
    return False

next_words = dict()
prev_words = dict()

prev = ""

output = open('bigrams_next.txt', 'w')


def print_buf():
    for key in next_words.keys():
        sorted_next = sorted(next_words[key].items(), key=operator.itemgetter(1))
        length = len(sorted_next)
        if length == 0:
            continue
        output.write(key + ' ')
        size = min(10, len(sorted_next))

        for i in range(size):
            output.write(sorted_next[length - size + i][0] + ' ')
            output.write(str(sorted_next[length - size + i][1]))
            output.write(' ')
        output.write('\n')

with open('all_texts_2.in') as f:
    number_of_lines = 1
    for line in f:
        if number_of_lines % B == 0:
            print_buf()
            next_words = dict()

        print("Line #" + str(number_of_lines))
        for word in line.split(" "):
            word = clear_word(word)
            if not is_word(word):
                continue

            if word not in next_words:
                next_words[word] = dict()
            if prev not in next_words:
                next_words[prev] = dict()

            if prev == "":
                prev = word
                continue

            if word not in next_words[prev]:
                next_words[prev][word] = 1
            else:
                next_words[prev][word] += 1

            prev = word
        number_of_lines += 1

print_buf()
