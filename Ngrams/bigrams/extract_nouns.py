import pymorphy2
import operator

morph = pymorphy2.MorphAnalyzer()

word_tags = dict()
normal_forms = dict()

next_words = dict()

with open('../../BIG_files/2grams-3.txt', encoding='utf-8') as f:
    for line in f:
        line = line.rstrip("\n")
        line = line.replace("\t\t", " ")
        line = line.replace("\t", " ")

        data = line.split(" ")
        normal_form = ''
        print(data)
        if data[2] in normal_forms:
            normal_form = normal_forms[data[2]]
        else:
            normal_form = morph.parse(data[2])[0].normal_form
            normal_forms[data[2]] = normal_form
            word_tags[normal_form] = morph.parse(normal_form)[0].tag

        tags = []
        if data[1] in word_tags:
            tags = word_tags[data[1]]
        else:
            tags = morph.parse(data[1])[0].tag
            word_tags[data[1]] = tags

        if 'PREP' in tags or 'CONJ' in tags or 'NPRO' in tags or 'PRCL' in tags:
            continue

        if 'NOUN' not in word_tags[normal_form]:
            continue



        freq = int(data[0])
        if data[2] not in next_words:
            next_words[data[2]] = dict()
        if data[1] not in next_words[data[2]]:
            next_words[data[2]][data[1]] = freq
        else:
            next_words[data[2]][data[1]] += freq

g = open('ruscorp_bigrams_reordered.txt', 'w', encoding='utf-8')

for word in next_words.keys():
    sorted_next = sorted(next_words[word].items(), key=operator.itemgetter(1), reverse=True)
    length = len(sorted_next)
    if length == 0:
        continue
    g.write(word + ' ')
    size = min(15, len(sorted_next))
    was = [False] * size
    for i in range(size):
        word = sorted_next[i][0]
        norm = morph.parse(word)[0].normal_form
        for j in range(i + 1, size):
            cur_word = sorted_next[j][0]
            normal_form = morph.parse(cur_word)[0].normal_form
            if norm == normal_form:
                was[j] = True
                sorted_next[i] = (sorted_next[i][0], sorted_next[i][1] + sorted_next[j][1])

    for i in range(size):
        if was[i]:
            continue
        g.write(sorted_next[i][0] + ' ')
        g.write(str(sorted_next[i][1]))
        g.write(' ')
    g.write('\n')

