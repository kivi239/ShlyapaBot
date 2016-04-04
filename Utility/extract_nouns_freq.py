import pymorphy2
import operator

morph = pymorphy2.MorphAnalyzer()

freq = dict()

with open('../synonymdict/1grams-3.txt', encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        data = line.split("\t")
        print(data)
        word = data[1]
        tags = morph.parse(word)[0].tag
        if 'NOUN' not in tags:
            continue
        word = morph.parse(word)[0].normal_form
        if word not in freq:
            freq[word] = int(data[0])
        else:
            freq[word] += int(data[0])

f = open('../synonymdict/dict_of_words.txt', encoding="utf-8", mode='w')

sorted_nouns = sorted(freq.items(), key=operator.itemgetter(1))
for i in range(len(sorted_nouns)):
    id = len(sorted_nouns) - i - 1
    try:
        f.write(str(sorted_nouns[id][1]) + " " + sorted_nouns[id][0])
        f.write("\n")
    except UnicodeEncodeError:
        print("can't encode")
    if sorted_nouns[id][1] < 10:
        break


