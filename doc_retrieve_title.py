#!/usr/bin/env python
# coding: utf-8

from os.path import join
import re
import json
import pickle
from time import time

from difflib import SequenceMatcher

from allennlp.models.archival import load_archive
from allennlp.predictors import Predictor


def get_predictor():
    """ Example:
        predictor = get_predictor()
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


def title_without_parentheses(title):
    return re.sub('-LRB-.*-RRB-', '', title).strip('_')


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


def load_titles(path, f_title):
    titles = pickle.load(open(join(path, f_title), "rb"))
    print("the number of titles:", len(titles))

    without_parentheses = {}
    for tid, title in titles.items():
        tit = title_without_parentheses(title)
        if title != tit:
            without_parentheses[tit] = tid

    titles.update(without_parentheses)

    print("get new processed titles without parentheses:",
          len(without_parentheses))
    print("after adding titles without parentheses:", len(titles))

    return titles


def result_stat(evidence, NPs, found_evidence):
    missing = []
    matched_titles = []
    for evi in evidence:
        got = False
        for NP in NPs:
            if NP in evi:
                got = True
                matched_titles.append(evi)
                break
        if got:
            found_evidence += 1
        else:
            missing.append(evi)

    return found_evidence, matched_titles, missing


def log_missing(missing):
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


DIR = './objects'
TITLES = 'titles_gensim_70.pkl'
DATA_SET = './devset.json'
OUTPUT_FILE = './output_devset_title.json'


if __name__ == '__main__':
    """ Calc doc retrieval accuracy """

    start = time()

    titles = load_titles(DIR, TITLES)
    predictor = get_predictor()

    with open(DATA_SET, 'r') as data_set_f:
        data_set = json.load(data_set_f)

    found_evidence, predicted_evidence, true_evidence = 0, 0, 0
    output_content, index = {}, 1
    for id_, record in data_set.items():
        evidence = list(map(lambda x: x[0], record['evidence']))
        true_evidence += len(evidence)

        parse_result = predictor.predict_json({"sentence": record['claim']})
        NPs = get_constituency_parsing_NPs(parse_result)
        NPs = get_customised_NPs(parse_result, NPs=NPs)

        found_evidence, matched_titles, missing = result_stat(evidence,
                                                              NPs,
                                                              found_evidence)
        predicted_evidence += len(matched_titles)
        # TODO: sentence selection
        record['evidence'] = [[title, 0] for title in matched_titles]
        output_content[id_] = record
        log_missing(missing)

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
        output_file.write(json.dumps(output_content))


