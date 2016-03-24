import logging
import pymorphy2

dictionary = "./bigrams_with_nouns.txt"
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

bigrams = {}
morph = pymorphy2.MorphAnalyzer()

def normal_form( word):
    norm = morph.parse(word)[0].normal_form
    return norm

with open(dictionary) as fil:
    r_pr = 0
    for line in fil.readlines():
        r_pr += 1
        if r_pr % 5000 == 0:
            logging.info(str(r_pr) + " direct bigrams processed")
        adj = line.split()[0]
        nouns = line.split()[1:]
        for noun0, noun1 in zip(nouns[0::2], nouns[1::2]):
            snf = normal_form(noun0)
            if snf not in bigrams:
                bigrams[snf] = {}
            if adj not in bigrams[snf]:
                bigrams[snf][adj] = noun1
            else:
                bigrams[snf][adj] += noun1

with open('./bigrams_with_nouns_reordered.txt', 'w') as f:
    for word in bigrams.keys():
        f.write(word)
        for key_ in bigrams[word].keys():
            f.write(" " + key_ + " " + str(bigrams[word][key_]))
        f.write("\n")
