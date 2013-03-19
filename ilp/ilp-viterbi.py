import sys
import re
import math
from lpsolve55 import *

def set_viterbi_obj_fun(sent):
    obj_fun = []
    index_map = {}
    var_index = 0
    token_index = 0
    
    for line in sent:
        for label_pair, score in line[1].iteritems():
            obj_fun.append(math.log(score))
            index_map[(token_index, label_pair)] = var_index
            var_index += 1
        token_index += 1
        
    return obj_fun, index_map
    
def set_prob_obj_fun(sentence, weight, var_offset = 0):
    obj_fun = []
    index_map = {}
    var_index = var_offset
    token_index = 0
    
    for line in sentence:
        for label, prob in line[1].iteritems():
            obj_fun.append(weight * math.log(prob))
            index_map[(token_index, label)] = var_index
            # print token_index, label, var_index
            var_index += 1
        token_index += 1
        
    return obj_fun, index_map

def set_penalty_obj_fun(aligns, penalties, var_offset = 0):
    obj_fun = []
    index_map = {}
    var_index = var_offset
    
    for (zh_index, en_index, align_prob) in aligns:
        for (zh_label, en_label), score in penalties.iteritems():
            if float(align_prob) > float(sys.argv[4]):
                obj_fun.append(math.log(score) * float(align_prob))
                index_map[(int(zh_index), int(en_index), zh_label, en_label)] = var_index
                # print int(zh_index), int(en_index), zh_label, en_label, var_index
                var_index += 1
    return obj_fun, index_map
    
def constraints_1(lp, sentence, var_num, var_offset = 0):
    ''' Set constraints that only one label for each token
    '''
    var_index = var_offset
    for line in sentence:
        constraint = [0] * var_num
        for label, prob in line[1].iteritems():
            constraint[var_index] = 1
            var_index += 1  
        lpsolve('add_constraint', lp, constraint, EQ, 1)

def constraints_unique(lp, sentence, var_num, var_offset = 0):
    ''' Set constraints that only one label for each token
    '''
    var_index = var_offset
    for line in sentence:
        constraint = [0] * var_num
        for label_pair, score in line[1].iteritems():
            constraint[var_index] = 1
            var_index += 1  
        lpsolve('add_constraint', lp, constraint, EQ, 1)

def constraints_IXX(lp, sentence, var_num, var_offset = 0):
    ''' Set constraints that I-XXX must follow B-XXX or I-XXX
    '''
    var_index = var_offset
    for line in sentence:
        constraint = [0] * var_num
        for (label1, label2), score in line[1].iteritems():
            if label2[:2] == 'I-' and label1[2:] != label2[2:]:
                constraint[var_index] = 1
            var_index += 1  
        lpsolve('add_constraint', lp, constraint, EQ, 0)

def constraints_2(lp, sentence, var_num, var_offset = 0):
    ''' Set constraints: z_{i, O} + z_{i+1, I-XXX} <= 1
    '''
    var_index = var_offset
    for token_index in range(len(sentence) - 1):
        constraint = [0] * var_num
        for label, prob in sentence[token_index][1].iteritems():
            if label == 'O':
                constraint[var_index] = 1
            var_index += 1

        offset = 0
        for label, prob in sentence[token_index + 1][1].iteritems():
            if re.match('^I-', label):
                constraint2 = constraint[:]
                constraint2[var_index + offset] = 1
                lpsolve('add_constraint', lp, constraint2, LE, 1)
            offset += 1

def constraints_3(lp, sentence, var_num, var_offset = 0):
    ''' Set constraints: z_{i, B-XXX} + z_{i, I-XXX} - z_{i+1, I-XXX} >= 0
    '''
    var_index = var_offset
    for line_index in range(len(sentence) - 1):
        constraints = {}
        for label, prob in sentence[line_index][1].iteritems():
            m = re.match('^[B|I]-(.+)$', label)
            if m:
                label = m.group(1)
                if label not in constraints:
                    constraints[label] = [0] * var_num
                constraints[label][var_index] = 1
            var_index += 1

        offset = 0
        for label, prob in sentence[line_index + 1][1].iteritems():
            m = re.match('^I-(.+)$', label)
            if m:
                label = m.group(1)
                if label in constraints:
                    constraint3 = constraints[label]
                    constraint3[var_index + offset] = -1
                    lpsolve('add_constraint', lp, constraint3, GE, 0)
            offset += 1

def constraints_viterbi(lp, sent, var_num):
    ''' Set constraints: z_{i, label2} = z_{i+1, label1}
    '''
    var_index = 0
    for line_index in range(len(sent) - 1):
        constraints = {}
        for (label1, label2), score in sent[line_index][1].iteritems():
            if label2 not in constraints:
                constraints[label2] = [0] * var_num
            constraints[label2][var_index] = 1
            var_index += 1

        offset = 0
        constraint_viterbi = {}
        for (label1, label2), score in sent[line_index + 1][1].iteritems():
            if label1 in constraints:
                constraint_viterbi[label1] = constraints[label1]
                constraint_viterbi[label1][var_index + offset] = -1
            offset += 1
        for item in constraint_viterbi.itervalues():
            lpsolve('add_constraint', lp, item, EQ, 0)

def constraints_4(lp, penalty_index_map, var_number):
    ''' Set constraints: Each word alignment pair can only have one penalty
    '''
    constraints = {}
    
    for (zh_index, en_index, zh_label, en_label), var_index in penalty_index_map.iteritems():
        if (zh_index, en_index) in constraints:
            constraints[(zh_index, en_index)].append(var_index)
        else:
            constraints[(zh_index, en_index)] = [var_index]
    for var_indexs in constraints.itervalues():
        constraint = [0] * var_number
        for var_index in var_indexs:
            constraint[var_index] = 1
        lpsolve('add_constraint', lp, constraint, EQ, 1)
        
def constraints_5(lp, zh_index_map, en_index_map, penalty_index_map, var_number):
    ''' Set constraints: labels in word alignment should be equal to sentence
    '''
    for (zh_index, en_index, zh_label, en_label), align_var_index in penalty_index_map.iteritems():
        constraint = [0] * var_number
        constraint[align_var_index] = 1
        
        zh_constraint = constraint[:]
        if zh_label != 'O':
            zh_constraint[zh_index_map[(zh_index, 'B-' + zh_label)]] = -1
            zh_constraint[zh_index_map[(zh_index, 'I-' + zh_label)]] = -1
        else:
            zh_constraint[zh_index_map[(zh_index, zh_label)]] = -1
        lpsolve('add_constraint', lp, zh_constraint, LE, 0)
        
        en_constraint = constraint[:]
        if en_label != 'O':
            en_constraint[en_index_map[(en_index, 'B-' + en_label)]] = -1
            en_constraint[en_index_map[(en_index, 'I-' + en_label)]] = -1
        else:
            en_constraint[en_index_map[(en_index, en_label)]] = -1
        lpsolve('add_constraint', lp, en_constraint, LE, 0)
    
def get_labels(sent, index_map, variables):
    labels = []
    token_index = 0
    
    for line in sent:
        for label, prob in line[1].iteritems():
            if variables[index_map[(token_index, label)]] == 1:
                labels.append(label)
        token_index += 1
    return labels

def get_viterbi_labels(sent, index_map, variables):
    labels = []
    token_index = 0
    
    for line in sent:
        for (label1, label2), prob in line[1].iteritems():
            if variables[index_map[(token_index, (label1, label2))]] == 1:
                labels.append(label2)
        token_index += 1
    return labels

def viterbi_output(sent, labels):
    if len(labels) != len(sent):
        labels = ['O'] * len(sent)

    index = 0
    for label in labels:
        sys.stdout.write(sent[index][0] + '\t' + label + '\n')
        index += 1
    
    sys.stdout.write('\n')

def bi_output(zh_sent, en_sent, zh_labels, en_labels):
    if len(zh_labels) != len(zh_sent) or len(en_labels) != len(en_sent):
        zh_labels = ['O'] * len(zh_sent)
        en_labels = ['O'] * len(en_sent)

    index = 0
    for label in zh_labels:
        sys.stdout.write(zh_sent[index][0] + '\t' + label + '\n')
        index += 1
    
    index = 0
    for label in en_labels:
        sys.stderr.write(en_sent[index][0] + '\t' + label + '\n')
        index += 1
        
    sys.stdout.write('\n')
    sys.stderr.write('\n')

def mono_viterbi_infer(sent):
    obj_fun, index_map = set_viterbi_obj_fun(sent)
    
    var_num = len(obj_fun)
    lp = lpsolve('make_lp', 0, len(obj_fun))

    for i in range(len(obj_fun)):
        lpsolve('set_binary', lp, i + 1, True)

    lpsolve('set_maxim', lp)
    lpsolve('set_verbose', lp, NEUTRAL)
    # lpsolve('set_verbose', lp, FULL)
    lpsolve('set_add_rowmode', lp, True)
    lpsolve('set_obj_fn', lp, obj_fun)

    constraints_unique(lp, sent, var_num)
    constraints_viterbi(lp, sent, var_num)
    constraints_IXX(lp, sent, var_num)

    lpsolve('set_add_rowmode', lp, False)
    lpsolve('write_lp', lp, 'ne.lp')
    lpsolve('solve', lp)
    # print lpsolve('get_objective', lp)
    variables = lpsolve('get_variables', lp)[0]
    labels = get_viterbi_labels(sent, index_map, variables)
    viterbi_output(sent, labels)
    lpsolve('delete_lp', lp)
  
def bili_inference(zh_sent, en_sent, aligns, penalties):    
    zh_prob_obj_fun, zh_index_map = set_prob_obj_fun(zh_sent, 1)
    en_prob_obj_fun, en_index_map = set_prob_obj_fun(en_sent, 1, len(zh_prob_obj_fun))
    penalty_obj_fun, penalty_index_map = set_penalty_obj_fun(aligns, penalties, len(zh_prob_obj_fun) + len(en_prob_obj_fun))
    
    obj_fun = zh_prob_obj_fun[:]
    obj_fun.extend(en_prob_obj_fun)
    obj_fun.extend(penalty_obj_fun)
    
    var_number = len(obj_fun)
    
    lp = lpsolve('make_lp', 0, len(obj_fun))

    for i in range(len(obj_fun)):
        lpsolve('set_binary', lp, i + 1, True)

    lpsolve('set_maxim', lp)
    lpsolve('set_verbose', lp, NEUTRAL)
    # lpsolve('set_verbose', lp, FULL)
    lpsolve('set_add_rowmode', lp, True)
    lpsolve('set_obj_fn', lp, obj_fun)
    
    constraints_1(lp, zh_sent, var_number)
    constraints_1(lp, en_sent, var_number, len(zh_prob_obj_fun))
    
    constraints_2(lp, zh_sent, var_number)
    constraints_2(lp, en_sent, var_number, len(zh_prob_obj_fun))
    
    constraints_3(lp, zh_sent, var_number)
    constraints_3(lp, en_sent, var_number, len(zh_prob_obj_fun))
    
    constraints_4(lp, penalty_index_map, var_number)
    
    constraints_5(lp, zh_index_map, en_index_map, penalty_index_map, var_number)

    lpsolve('set_add_rowmode', lp, False)
    # lpsolve('write_lp', lp, 'ne.lp')
    lpsolve('solve', lp)
    # print lpsolve('get_objective', lp)
    variables = lpsolve('get_variables', lp)[0]
    zh_labels = get_labels(zh_sent, zh_index_map, variables)
    en_labels = get_labels(en_sent, en_index_map, variables)
    bi_output(zh_sent, en_sent, zh_labels, en_labels)
    lpsolve('delete_lp', lp)

def next_sent(file_iter):
    sentence = []
    while True:
        line = file_iter.next().strip()
        if line == '':
            return sentence
        else:
            pieces = line.split('\t')
            token = pieces[0]
            labels_prob = {}
            for piece in pieces[1:]:
                (label, prob) = piece.split('=')
                labels_prob[label] = float(prob)
            sentence.append((token, labels_prob))

def next_clique_sent(file_iter):
    ''' format of a token: 
        token   label(i-1)_label(i)=score
    '''
    sentence = []
    while True:
        line = file_iter.next().strip()
        if line == '':
            return sentence
        else:
            pieces = line.split('\t')
            token = pieces[0]
            label_pairs_score = {}
            for piece in pieces[1:]:
                (label_pair, score) = piece.split('=')
                label_pairs_score[tuple(label_pair.split('_'))] = float(score)
            sentence.append((token, label_pairs_score))

def set_penalties(file):
    penalties = {}
    for penalty in file:
        (zh_label, en_label, p) = penalty.strip().split('\t')
        p = float(p)
        penalties[(zh_label, en_label)] = p
    return penalties
    
def bili_process():
    zh_ne_iter = iter(open(sys.argv[1]))
    en_ne_iter = iter(open(sys.argv[2]))
    align_iter = iter(open(sys.argv[3]))
    penalties = set_penalties(open(sys.argv[5]))

    try:
        while True:
            zh_sent = next_sent(zh_ne_iter)
            en_sent = next_sent(en_ne_iter)
            aligns = [word_align.split(':') for word_align in align_iter.next().split()]
            bili_inference(zh_sent, en_sent, aligns, penalties)
    except StopIteration:
        pass

def mono_viterbi():
    ne_iter = iter(open(sys.argv[1]))
    try:
        while True:
            sent = next_clique_sent(ne_iter)
            mono_viterbi_infer(sent)
    except StopIteration:
        pass
            
if __name__ == '__main__':
    if len(sys.argv) == 6:
        bili_process()
    elif len(sys.argv) == 2:
        mono_viterbi()
    else:
        print ''' Usage: \n\t python ilp-soft.py mono_NE_prob_file_ZH mono_NE_prob_file_EN word_alignment_file threshold penalty_file
              '''






