import pymorphy2
import operator

FREQ = 5 #ignore

morph = pymorphy2.MorphAnalyzer()

next_words = dict()

output = open('bigrams_with_nouns.txt', 'w')


def print_buf():
    cnt = 0
    print("Saving to file")
    size = len(next_words.keys())
    for key in next_words.keys():
        print(str(cnt) + " out of " + str(size))
        sorted_next = sorted(next_words[key].items(), key=operator.itemgetter(1))
        length = len(sorted_next)
        if length == 0:
            continue
        if int(sorted_next[length - 1][1]) < FREQ:
            continue
        output.write(key + ' ')
        size = min(10, len(sorted_next))

        for i in range(size):
            if int(sorted_next[length - size + i][1]) < FREQ:
                continue
            output.write(sorted_next[length - size + i][0] + ' ')
            output.write(str(sorted_next[length - size + i][1]))
            output.write(' ')
        output.write('\n')
        cnt += 1

with open('bigrams_next.txt') as f:
    cnt = 0
    for line in f:
        print("Word #" + str(cnt) + "\n")
        data = line.split(" ")
        if len(data) == 0:
            continue
        key = data[0]
        if key not in next_words:
            next_words[key] = dict()
        for i in range(1, len(data) // 2):
            word = data[2 * i - 1]
            count = int(data[2 * i])
            tags = morph.parse(word)[0].tag
            if 'NOUN' in tags:
                if word not in next_words[key]:
                    next_words[key][word] = count
                else:
                    next_words[key][word] += count
        cnt += 1

print_buf()