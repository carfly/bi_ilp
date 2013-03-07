import random
import sys

def read_sentences(sentences, filename):
    with open(filename) as file:
        sentence = ''
        for line in file:
            if line.strip() == '':
                sentences.append(sentence)
                sentence = ''
            else:
                sentence += line
    file.close()

def main(filename, number):
    sentences = []

    read_sentences(sentences, filename)

    # random.shuffle(sentences)

    i = 0
    for sentence in sentences:
        if i < number:
            print sentence
            i += 1
        else:
            return

if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], int(sys.argv[2]))
    else:
        print '''Usage: \n\t python select_top.py file number'''
