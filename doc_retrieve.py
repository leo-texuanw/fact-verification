#!/usr/bin/env python
# coding: utf-8

from os.path import join
import re
import json

from tqdm import tqdm

from allennlp.models.archival import load_archive
from allennlp.predictors import Predictor

import xdb_query

TRAIN_SET = './train.json'
DEV_SET = './devset.json'

archive = load_archive(
    "https://s3-us-west-2.amazonaws.com/allennlp/models/elmo-constituency-parser-2018.03.14.tar.gz")
predictor = Predictor.from_archive(archive, 'constituency-parser')


# Evaluate doc retrieval
def get_constituency_parsing_NPs(parse_result, NPs=set()):
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
            NPs.add(" ".join(NP))
            NP = []

    if NP:
        NPs.add(" ".join(NP))

    return NPs


def get_customised_NPs(parse_result, ignore_list, NPs=set()):
    """ get NPs by customised rules according to POS """

    NP = []
    pos_tags = parse_result['pos_tags']
    tokens = parse_result['tokens']

    for id_, tag in enumerate(pos_tags):
        if tag in ['NP', 'NNP', 'HYPH']:
            NP.append(tokens[id_])
        elif tag in ignore_list:
            NP.append(tag)
        elif NP:
            NPs.add(" ".join(NP))
            NP = []

    if NP:
        NPs.add(" ".join(NP))

    return NPs


def load_json_file(path):
    with open(path, 'r') as json_file:
        json_obj = json.load(json_file)
    return json_obj


def doc_retrieval(record, db_path, ignore_list):
    parse_result = predictor.predict_json({"sentence": record['claim']})
    NPs = get_constituency_parsing_NPs(parse_result)
    NPs = get_customised_NPs(parse_result, ignore_list, NPs)

    docs = []
    for NP in NPs:
        print("NP:", NP)
        matches = xdb_query.search(db_path, NP, "title")
        xdb_query.print_matches(matches)
        docs.append(matches)

    return docs


if __name__ == '__main__':
    DB_PATH = './xdb/wiki.db'
    ignore_list = ['-LRB-', '-RRB-']
    dev_set = load_json_file(DEV_SET)

    for id_, record in tqdm(dev_set.items()):
        docs = doc_retrieval(record, DB_PATH, ignore_list)
        # TODO
        # get titles
        # write to ourput file
        break
# TODO: trying to adopt the following code


# found_evidence, total_evidence, true_evidence = 0, 0, 0
# for _id, record in tqdm(train_set.items()):
#     evidence = list(map(lambda x: x[0], record['evidence']))
#     true_evidence += len(evidence)
#
#     parse_result = predictor.predict_json({"sentence": record['claim']})
#     NPs = get_NPs(parse_result)
#     total_evidence += len(NPs)
#
#     # TODO: search NP in xapian, get result
#     # calc result in evidence
#     missing = []
#     for evi in evidence:
#         got = False
#         for NP in NPs:
#             if NP in evi:
#                 got = True
#                 break
#         if got:
#             found_evidence += 1
#         else:
#             missing.append(evi)
#
#     if missing:
#         print('In claim:', record['claim'])
#         print('    NPs:', NPs)
#         print('    missing:', missing)
#         # print('    POS:', (pred_result['hierplane_tree']['root']['children']))
#         print('    POS:', parse_result['pos_tags'])

# sentence = "Nikolaj Coster-Waldau worked with the Fox Broadcasting Company."
# result = predictor.predict_json({"sentence": sentence})
#
# print(result.keys())
# pos_tags = result['pos_tags']
# print(pos_tags)
# tokens = result['tokens']
# print(tokens)
#
#
# print(result['hierplane_tree']['root'])
# # keys of result['hierplane_tree']['root']: ['word', 'nodeType', 'attributes', 'link', 'children']
# for child in result['hierplane_tree']['root']['children']:
#     print(child)
