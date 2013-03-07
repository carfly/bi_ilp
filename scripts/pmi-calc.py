import sys
import re

def next_sent(file_iter):
    sentence = []
    while True:
        line = file_iter.next().strip()
        if line == '':
            return sentence
        else:
            token, label = line.split('\t')
            sentence.append(label[:])
def count_label_pairs(zh_sent, en_sent, aligns, label_pairs):
    for align in aligns:
        zh_index = int(align[0])
        en_index = int(align[1])
        zh_label = zh_sent[zh_index][2:] if zh_sent[zh_index][2:] != '' else zh_sent[zh_index]
        en_label = en_sent[en_index][2:] if en_sent[en_index][2:] != '' else en_sent[en_index]
        if (zh_label, en_label) in label_pairs:
            label_pairs[(zh_label, en_label)] += 1
        else:
            label_pairs[(zh_label, en_label)] = 1
    
def statistic(label_pairs):
    C2E = {}
    E2C = {}
    count_all = sum(label_pairs.values())

    for (zh_label, en_label), count in label_pairs.iteritems():
        # print zh_label, en_label, count
        if zh_label in C2E:
            C2E[zh_label] += count
        else:
            C2E[zh_label] = count
            
        if en_label in E2C:
            E2C[en_label] += count
        else:
            E2C[en_label] = count

    for (zh_label, en_label), count in label_pairs.iteritems():
        print '%s\t%s\t%f' % (zh_label, en_label, float(count) * count_all / (C2E[zh_label] * E2C[en_label]))
    
def process():
    zh_ne_iter = iter(open(sys.argv[1]))
    en_ne_iter = iter(open(sys.argv[2]))
    align_iter = iter(open(sys.argv[3]))

    label_pairs = {}
    try:
        while True:
            zh_sent = next_sent(zh_ne_iter)
            en_sent = next_sent(en_ne_iter)
            aligns = [word_align.split('-') for word_align in align_iter.next().split()]
            count_label_pairs(zh_sent, en_sent, aligns, label_pairs)
    except StopIteration:
        pass
    
    statistic(label_pairs)

if __name__ == '__main__':
    if len(sys.argv) == 4:
        process()
    else:
        print ''' Usage: \n\t python pmi-calc.py zh.ner.test.answer en.ner.test.answer word_alignment_file 
                  e.g. python pmi-calc.py zh.ner.test.crf.out en.ner.test.crf.out corpus.HMM.t0.8.align '''






