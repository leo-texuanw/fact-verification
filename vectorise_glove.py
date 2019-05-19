#!/usr/bin/env python
# coding: utf-8

import csv
from time import time
from os.path import join
from functools import partial, reduce

import pandas as pd
import numpy as np

TOOL_PATH = './tools'
GLOVE_840 = 'glove.840B.300d.txt'


def load_glove(path):
    return pd.read_csv(
            path,
            sep=" ",
            index_col=0,
            header=None,
            quoting=csv.QUOTE_NONE)


def get_word_vec(word, glove):
    """ get word embedding of a word """

    try:
        return glove.loc[word].as_matrix()
    except KeyError as _e:
        return glove.loc['unk'].as_matrix()


def words_avg_embedding(words: list, glove):
    """ get average word embedding of a list of words """

    word_embeddings = map(partial(get_word_vec, glove=glove), words)
    sum_words_embedding = reduce(np.add, word_embeddings)
    return sum_words_embedding / len(words)


def words_embedding(words: list, glove):
    """ get concatenated word embeddings of a list of words """

    word_embeddings = map(partial(get_word_vec, glove=glove), words)
    concat_words_embedding = np.concatenate(list(word_embeddings))
    return concat_words_embedding


if __name__ == '__main__':
    start = time()
    glove = load_glove(join(TOOL_PATH, GLOVE_840))
    print("load glove:", time() - start, "seconds")
    print(len(glove), "lines in glove")

    words = ['hello', 'world', '!']
    words_avg_embedding = words_avg_embedding(words, glove)
    assert(len(words_avg_embedding) == 300)

    words_embedding = words_embedding(words, glove)
    assert(len(words_embedding) == 300 * len(words))
