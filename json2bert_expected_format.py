# This file is for transforming json dataset to the format what BERT expect.

import sys
import json

from tqdm import tqdm

from constants import Args
import xdb_query
import doc_retrieve_title as drt


def get_sents_from_doc(doc, sent_ids, lines):
    # get evidence sents from doc
    for sent_id in sent_ids:
        sent = doc['sentences'].get(str(sent_id), "")

        if sent:
            lines.append(sent)
        else:
            print("--------sent_id---------", sent_id, "not in", doc)
    return lines


def get_content_from_db(d_titles, title_2_sent_ids, transform4label):
    lines = []

    for title, sent_ids in title_2_sent_ids.items():
        # get title's docid in db
        docid = drt.get_doc_id(d_titles, title)

        if docid:
            # get doc in db
            doc = xdb_query.get_document(Args.DB_PATH, docid)
        else:
            # TODO: solve encoding, e.g. `José_María_Chacón`
            continue

        try:
            doc = json.loads(doc.get_data())
        except:
            print("------------docid:------------", docid, "not exist in db")
            continue

        if transform4label:
            lines = get_sents_from_doc(doc, sent_ids, lines)
        else:
            for sent_id, sent in doc['sentences'].items():
                label = 'yes' if int(sent_id) in sent_ids else 'no'
                lines.append([sent_id, label, sent, title])

    return lines


if __name__ == '__main__':
    d_titles = xdb_query.load_xapian_titles(Args.OBJECTS, Args.TITLES)
    idx, transform4label = 0, True

    fin = open(sys.argv[1], 'r')
    fout = open(sys.argv[2], 'w')

    data_set = json.load(fin)
    for id_, record in tqdm(data_set.items()):
        claim = record['claim']
        l_evidence = record['evidence']

        title_2_sent_ids = {}           # {title: [sent_id, ...]}
        for title, sent_id in l_evidence:
            title_2_sent_ids[title] = title_2_sent_ids.get(title, []) + [sent_id]
        else:
            # label "NOT ENOUGH INFO" has no evidence,
            # so search the most relevent doc by claim according to xapian db
            match = xdb_query.search(Args.DB_PATH, claim, pagesize=1)[0]

        if l_evidence:
            # get sentences from database according to title, sentence ids
            # transform4label is related to the format of returned content
            content = get_content_from_db(d_titles,
                                          title_2_sent_ids,
                                          transform4label)
            if not content:
                print(title_2_sent_ids, '\n')
        else:
            # if no evidence given by the data set, get content of the doc
            # that xapian thinks it's most relevant
            doc = json.loads(match[2])
            title = doc['title']
            content, label = [], 'no'

            for sent_id, sent in doc['sentences'].items():
                if transform4label:
                    content.append(sent)
                else:
                    content.append([sent_id, label, sent, title])

        # write data back according to if the task is for labeling or sentence
        # selection
        if transform4label:
            label = record.get('label', 'label')
            content = " ".join(content)
            example = "\t".join([id_, label, claim, content])
            fout.write(example + "\n")
        else:
            i = 0
            for (sent_id, label, sent, title_of_sent) in content:
                # make example id as claim id concated with sentence id
                example_id = "{}{:0>3}".format(id_, i)
                elems = [example_id, label, claim, sent, title_of_sent, sent_id]
                example = "\t".join(elems)
                fout.write(example + "\n")
                i += 1

            idx += 1

    fin.close()
    fout.close()
