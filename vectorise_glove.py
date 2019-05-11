#!/usr/bin/env python
# coding: utf-8

from os import listdir
from os.path import join
from functools import partial, reduce
from multiprocessing import Pool

from time import time
from tqdm import tqdm

import csv
import pandas as pd
import numpy as np

def load_glove(path):
    return pd.read_csv(path, sep=" ", index_col=0, header=None, quoting=csv.QUOTE_NONE)

def load_corpus(file_path, file_name):
    docs = {}
    with open(join(file_path, file_name), 'r') as f:
        for line in f:
            line = line.strip('\n').split(' ')
            title = line[0]
            docs[title] = docs.get(title, []) + line[2:]
    return docs

def get_word_vec(word, glove):
    try:
        return glove.loc[word].as_matrix()
    except:
        return glove.loc['unk'].as_matrix()


def doc_embedding(doc, glove):
    word_embeddings = map(partial(get_word_vec, glove=glove), doc)
    sum_doc_embedding = reduce(np.add, word_embeddings)
    return sum_doc_embedding / len(doc)


def process_corpus_with_glove(file_name, file_path, dest_path, glove):
    with open(join(dest_path, file_name), 'w') as dest_f:
        docs = load_corpus(file_path, file_name)

        for title, doc in tqdm(docs.items()):
            doc = doc_embedding(doc, glove)
            temp = " ".join(map(str, doc.tolist()))
            dest_f.write(title + " " + temp + '\n')
    print("finish file", file_name)


TOOL = './tools'
GLOVE_840 = 'glove.840B.300d.txt'
COURPUS_PATH = './wiki-pages-text/'
PROCESSED_CORPUS_GLOVE = './processed_wiki_glove'

start = time()
glove = load_glove(join(TOOL, GLOVE_840))
print("load glove:", time() - start, "seconds")

# line = ['title', 'hello', 'world']
# doc_embed = doc_embedding(line, glove)
# print(len(doc_embed))
# print(doc_embed)


data_files = listdir(COURPUS_PATH)

pool = Pool(processes=12)
pool.map(partial(process_corpus_with_glove,
                 file_path=COURPUS_PATH,
                 dest_path=PROCESSED_CORPUS_GLOVE,
                 glove=glove),
         data_files)
pool.close()
pool.join()


#process_corpus_with_glove(
#    data_files[0],
#    file_path=COURPUS_PATH,
#    dest_path=PROCESSED_CORPUS_GLOVE,
#    glove=glove)

