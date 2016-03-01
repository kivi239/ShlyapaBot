import pymorphy2

morph = pymorphy2.MorphAnalyzer()

result = open('synonyms_norm.txt', 'w')

with open('synonyms2.txt') as f:
    for line in f:
        for words in line.split("\t"):
            for word in words.split(" "):
                word = morph.parse(word.rstrip())[0].normal_form
                result.write(word + ' ')
        result.write('\n')
