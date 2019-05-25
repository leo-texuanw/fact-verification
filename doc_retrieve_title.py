#!/usr/bin/env python
# coding: utf-8

from os.path import join
import re
import json
import pickle
from time import time
from tqdm import tqdm

import spacy
from difflib import SequenceMatcher

from allennlp import pretrained
from allennlp.models.archival import load_archive
from allennlp.predictors import Predictor

import xdb_query


def get_constituency_parser():
    """ Example:
        predictor = get_constituency_parser()
        sentence = "Nikolaj Coster-Waldau worked with the Fox Broadcasting Company."
        result = predictor.predict_json({"sentence": sentence})

        print(result.keys()) # useful: 'pos_tags', 'tokens', 'hierplane_tree'

        print(result['hierplane_tree']['root'])
        # keys of result['hierplane_tree']['root']:
        #    ['word', 'nodeType', 'attributes', 'link', 'children']

        for child in result['hierplane_tree']['root']['children']:
            print(child)
    """
    archive = load_archive(
        "https://s3-us-west-2.amazonaws.com/allennlp/models/elmo-constituency-parser-2018.03.14.tar.gz")

    return Predictor.from_archive(archive, 'constituency-parser')


def get_decomposable_attention():
    archive = load_archive(
        "https://s3-us-west-2.amazonaws.com/allennlp/models/decomposable-attention-elmo-2018.02.19.tar.gz")

    return Predictor.from_archive(archive, 'decomposable-attention')


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def get_constituency_parsing_NPs(parse_result, join_with="_", NPs=set()):
    # TODO: 
    # 1. everything before verb as a NP
    # 2. deal with different encoding

    NP = []

    # by hierplane_tree
    hierplane_tree_children = parse_result['hierplane_tree']['root']['children']
    for child in hierplane_tree_children:
        if child['nodeType'] in ['NP', 'HYPH']:
            NP += child['word'].split()
        elif NP:
            NPs.add(join_with.join(NP))
            NP = []

    if NP:
        NPs.add(join_with.join(NP))

    return NPs


def get_customised_NPs(parse_result, join_with="_", NPs=set()):
    """ get NPs by customised rules according to POS """

    ignore_list = ['-LRB-', '-RRB-']
    NP = []
    pos_tags = parse_result['pos_tags']
    tokens = parse_result['tokens']

    for id_, tag in enumerate(pos_tags):
        if tag in ['NP', 'NNP', 'HYPH']:
            NP.append(tokens[id_])
        elif tag in ignore_list:
            NP.append(tag)
        elif NP:
            NPs.add(join_with.join(NP))
            NP = []

    if NP:
        NPs.add(join_with.join(NP))

    if join_with == "_":
        NPs = list(map(lambda NP: re.sub('_-_', '-', NP), NPs))
    return NPs


def title_without_parentheses(title):
    return re.sub('-LRB-.*-RRB-', '', title).strip('_')


def load_xapian_titles(path, f_title):
    titles = {}
    with open(join(path, f_title), 'r') as f:
        for line in f:
            doc_id, title = line.strip('\n').split('\t')
            titles[title] = doc_id
    print("the number of titles:", len(titles))

    # without_parentheses = {}
    # for title, tid in titles.items():
    #     tit = title_without_parentheses(title)
    #     if title != tit:
    #         without_parentheses[tit] = tid

    # titles.update(without_parentheses)

    # print("get new processed titles without parentheses:",
    #       len(without_parentheses))
    print("after adding titles without parentheses:", len(titles))

    return titles


def NPs2titles(NPs, titles_dict):
    # TODO: search unmatched in xapian
    return [titles_dict[NP] for NP in NPs if NP in titles_dict]


def result_stat(evidence, NPs, found_evidence):
    missing = []
    matched_titles = set()

    for evi in evidence:
        got = False
        for NP in NPs:
            if NP in evi:
                got = True
                matched_titles.add(evi)
                break
        if got:
            found_evidence += 1
        else:
            missing.append(evi)

    return found_evidence, list(matched_titles), missing


def log_missing(missing, record, NPs, parse_result):
    if missing:
        print('In claim:', record['claim'])
        print('    NPs:', NPs)
        print('    missing:', missing)
        print('    POS:', parse_result['pos_tags'])


def log_performance(index, true_evidence, found_evidence, predicted_evidence):
    print(index, ":")
    print(true_evidence, found_evidence, predicted_evidence)
    print("accuracy:", found_evidence / true_evidence)
    print("recall:", found_evidence / predicted_evidence)


def get_sents(doc_ids, db_path):
    candidates = []
    for doc_id in set(doc_ids):

        match = xdb_query.get_document(db_path, int(doc_id))
        match = json.loads(match.get_data())

        title = match.get('title', "")
        if not title:
            continue

        temp = [[title, sent_id, sent] for sent_id, sent in
                match.get('sentences', '').items() if sent]
        candidates += temp
    return candidates


def sent_selection_sim(nlp, claim, doc_ids, db_path, topn=10):
    candidates = get_sents(doc_ids, db_path)

    sents = []
    for title, sent_id, sent in candidates:
        if not sent:
            continue

        claim_ = nlp(claim)
        sent_ = nlp(sent)
        sim = claim_.similarity(sent_)
        # if sim > 0.4:  # TODO
        sents.append((sim, [title, int(sent_id)]))
    sents.sort(reverse=True)
    return [sent[1] for sent in sents[:topn]]


def sent_selection_entail(attention, claim, doc_ids, db_path, topn=10):
    candidates = get_sents(doc_ids, db_path)

    sents = []
    for title, sent_id, sent in candidates:
        if not sent:
            continue

        # [entailment, contradiction, neutral]
        probs = attention.predict(premise=sent, hypothesis=claim)['label_probs']
        # if max(probs[0:2]) > 0.4:  # TODO
        sents.append((max(probs[0:2]), [title, int(sent_id)]))
    sents.sort(reverse=True)
    return [sent[1] for sent in sents[:topn]]


def get_doc_ids(titles, matched_titles):
    return [titles[title] for title in matched_titles]


DIR = './objects'
TITLES = 'xapian_titles'  # 'titles_gensim_70.pkl'
DATA_SET = 'subdevset.json'  # './devset.json'
OUTPUT_FILE = './output_devset_title_test.json'
DB_PATH = './xdb/wiki.db'


if __name__ == '__main__':
    """ Calc doc retrieval accuracy """

    start = time()
    # print("loading embedding...")
    # nlp = spacy.load('en_vectors_web_lg')  # 300-dim GloVe vectors
    # TODO: change num_vector?
    # print("finished loading embedding...")

    titles_dict = load_xapian_titles(DIR, TITLES)
    predictor = get_constituency_parser()

    attention = pretrained.decomposable_attention_with_elmo_parikh_2017()

    with open(DATA_SET, 'r') as data_set_f:
        data_set = json.load(data_set_f)

    found_evidence, predicted_evidence, true_evidence = 0, 0, 0
    output_content, index = {}, 1
    for id_, record in tqdm(data_set.items()):
        evidence = list(map(lambda x: x[0], record['evidence']))
        true_evidence += len(evidence)

        parse_result = predictor.predict_json({"sentence": record['claim']})
        NPs = get_constituency_parsing_NPs(parse_result, NPs=set())
        NPs = get_customised_NPs(parse_result, NPs=NPs)

        doc_ids = NPs2titles(NPs, titles_dict)

        found_evidence, matched_titles, missing = result_stat(evidence, NPs, found_evidence)  # TODO
        predicted_evidence += len(doc_ids)

        # sents = sent_selection_sim(nlp, record['claim'], doc_ids, DB_PATH, 10)
        sents = sent_selection_entail(attention, record['claim'], doc_ids, DB_PATH, 15)
        record['evidence'] = sents
        log_missing(missing, record, NPs, parse_result)
        # record['evidence'] = [[title, 0] for title in matched_titles]
        output_content[id_] = record

        if index % 500 == 0:
            log_performance(index,
                            true_evidence,
                            found_evidence,
                            predicted_evidence)
        index += 1


    print("doc retrieval with titles takes",
          time() - start,
          "seconds except writ results down")

    with open(OUTPUT_FILE, 'w') as output_file:
        output_file.write(json.dumps(output_content, indent=2))
