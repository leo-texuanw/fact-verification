#!/usr/bin/env python
# coding: utf-8

# This file is for Information Retrieval.
# We used constituency parsing tree and part of speech to extract entities from
# claims and match them with wiki titles to do the document retrieval. 

import re
import json
from typing import List
from time import time
from tqdm import tqdm

import spacy

from allennlp import pretrained
from allennlp.models.archival import load_archive
from allennlp.predictors import Predictor

import xdb_query
from constants import Args


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


def get_constituency_parsing_NPs(parse_result, join_with="_", NPs=set()):
    """ get None Phrases by by hierplane_tree from constituency parsing """

    # TODO: 
    # 1. everything before verb as a NP
    # 2. deal with different encoding
    # 3. -COLON- ?

    NP = []
    hierplane_tree_children = parse_result['hierplane_tree']['root']['children']

    for child in hierplane_tree_children:
        # get continuous NP and HYPH as a NP
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

    NP = []
    remain_tag_list = ['-LRB-', '-RRB-']
    pos_tags = parse_result['pos_tags']
    tokens = parse_result['tokens']

    for id_, tag in enumerate(pos_tags):
        if tag in ['NP', 'NNP', 'HYPH']:
            NP.append(tokens[id_])
        elif tag in remain_tag_list:
            NP.append(tag)
        elif NP:
            NPs.add(join_with.join(NP))
            NP = []

    if NP:
        NPs.add(join_with.join(NP))

    if join_with == "_":
        NPs = list(map(lambda NP: re.sub('_-_', '-', NP), NPs))
    return NPs


def NPs2titles(NPs, titles_dict):
    # TODO: search unmatched in xapian
    return [titles_dict[NP] for NP in NPs if NP in titles_dict]


def result_stat(evidence, NPs):
    missing = []
    matched_titles = set()

    for evi in evidence:
        got = False
        for NP in NPs:
            if NP in evi:
                got = True
                matched_titles.add(evi)
                break
        if not got:
            missing.append(evi)

    return list(matched_titles), missing


def log_missing(missing, record, NPs, parse_result):
    if missing:
        print('In claim:', record['claim'])
        print('    NPs:', NPs)
        print('    missing:', missing)
        print('    POS:', parse_result['pos_tags'])


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


def sent_selection_esim(esim, claim, doc_ids, db_path, topn=10):
    candidates = get_sents(doc_ids, db_path)

    sents = []
    for title, sent_id, sent in candidates:
        if not sent:
            continue

        # [entailment, contradiction, neutral]
        probs = esim.predict(premise=sent, hypothesis=claim)['label_probs']
        # if max(probs[0:2]) > 0.4:  # TODO
        sents.append((max(probs[0:2]), [title, int(sent_id)]))
    sents.sort(reverse=True)
    return [sent[1] for sent in sents[:topn]]


def get_doc_id(d_titles: dict, title: str):
    try:
        doc_id = int(d_titles[title])
    except KeyError:
        # e.g. 'Simón_Bolívar'
        print("title:", title, "not found")
        doc_id = None

    return doc_id


def get_doc_ids(d_titles: dict, matched_titles: List[str]):
    doc_ids = []

    for title in matched_titles:
        doc_id = get_doc_ids(title)
        if doc_id:
            doc_ids.append(doc_id)

    return doc_ids


def IR(sent_select_method):
    if sent_select_method == 'esim':
        esim = pretrained.esim_nli_with_elmo_chen_2017()
    elif sent_select_method == 'entail':
        attention = pretrained.decomposable_attention_with_elmo_parikh_2017()
    else:
        print("loading embedding...")
        nlp = spacy.load('en_vectors_web_lg')  # 300-dim GloVe vectors
        # TODO: change num_vector?
        print("finished loading embedding...")

    titles_dict = xdb_query.load_xapian_titles(Args.OBJECTS, Args.TITLES)
    predictor = get_constituency_parser()

    with open(DATA_SET, 'r') as data_set_f:
        data_set = json.load(data_set_f)

    num_sents = 1
    print("num sents selected", num_sents)
    output_content = {}
    for id_, record in tqdm(data_set.items()):
        parse_result = predictor.predict_json({"sentence": record['claim']})

        NPs = get_constituency_parsing_NPs(parse_result, NPs=set())
        NPs = get_customised_NPs(parse_result, NPs=NPs)

        # doc_ids = NPs2titles(NPs, titles_dict)

        if Args.LOG_MISSING_DOCS:
            evidence = list(map(lambda x: x[0], record['evidence']))
            matched_titles, missing = result_stat(evidence, NPs)
            log_missing(missing, record, NPs, parse_result)

        # Sentence selection
        # if sent_select_method == 'esim':
        #     sents = sent_selection_esim(esim,
        #                                 record['claim'],
        #                                 doc_ids,
        #                                 Args.DB_PATH,
        #                                 num_sents)
        # elif sent_select_method == 'entail':   # texual entailment
        #     # not very well
        #     sents = sent_selection_entail(attention,
        #                                   record['claim'],
        #                                   doc_ids,
        #                                   Args.DB_PATH,
        #                                   num_sents)
        # else:                                   # similarity
        #     sents = sent_selection_sim(nlp,
        #                                record['claim'],
        #                                doc_ids,
        #                                Args.DB_PATH,
        #                                num_sents)  # 1 sent is the best

        # record['evidence'] = sents

        t = [NP for NP in NPs if NP in titles_dict]
        # randomly select 'sentence 0' from each doc to do doc retrieval
        record['evidence'] = [[title, 0] for title in t]
        output_content[id_] = record

    return output_content


# CHECK SETTINGS BEFORE EVERY TIME
DATA_SET = './data/devset.json'      # './subdevset.json'
OUTPUT_FILE = 'devset4bert_sent.json'  # './mysubdevset.json'


if __name__ == '__main__':
    """ Calc doc retrieval accuracy """

    start = time()

    sent_select_method = 'sim'  # ['sim', 'esim', 'entail']
    print("sent select method:", sent_select_method)
    output_content = IR(sent_select_method)

    print("doc retrieval with titles takes",
          time() - start,
          "seconds except writ results down")

    with open(OUTPUT_FILE, 'w') as output_file:
        output_file.write(json.dumps(output_content, indent=2))
