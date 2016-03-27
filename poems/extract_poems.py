vowels = ['а', 'е', 'ё', 'и', 'о', 'у', 'ы', 'э', 'ю', 'я']

MIN_VOWELS = 6
MAX_VOWELS = 15
MAX_DIFF_VOWELS = 3

def count_syllables(string):
    cnt = 0
    for c in string:
        c = c.lower()
        for v in vowels:
            if v == c:
                cnt += 1
                break
    return cnt


def write_poem(poem, file):
    if len(poem) <= 1:
        return -1
    for string in poem:
        file.write(string)
    file.write('\n')
    return 0

res = open('poems.txt', 'w')

with open('a_ahmat.txt') as f:
    cur_poem = []
    prev_cnt = -1
    for line in f:
        cnt = count_syllables(line)
        print(line.rstrip(" \n".lstrip(" \n")) + "# " + str(cnt))
        if (len(cur_poem) == 0 or abs(prev_cnt - cnt) <= MAX_DIFF_VOWELS) and MIN_VOWELS <= cnt <= MAX_VOWELS:
            cur_poem.append(line.rstrip(" ").lstrip(" "))
            prev_cnt = cnt
        else:
            write_poem(cur_poem, res)
            cur_poem = []
            prev_cnt = -1

