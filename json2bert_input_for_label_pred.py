import sys
import json

from constants import Args
import xdb_query
import doc_retrieve_title as drt


def concat_evidence(d_titles, title_2_sent_ids):
    sents = []

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

        # get evidence from doc
        for sent_id in sent_ids:
            sent = doc['sentences'].get(str(sent_id), "")

            if sent:
                sents.append(sent)
            else:
                print("--------sent_id---------", sent_id, "not in", doc)

    return " ".join(sents)


if __name__ == '__main__':
    d_titles = xdb_query.load_xapian_titles(Args.OBJECTS, Args.TITLES)

    fin = open(sys.argv[1], 'r')
    fout = open(sys.argv[2], 'w')

    data_set = json.load(fin)
    for id_, record in data_set.items():
        label = record.get('label', 'label')
        l_evidence = record['evidence']

        title_2_sent_ids = {}           # {title: [sent_id, ...]}
        for title, sent_id in l_evidence:
            title_2_sent_ids[title] = title_2_sent_ids.get(title, []) + [sent_id]
        else:
            # label "NOT ENOUGH INFO" has no evidence,
            # so search the most relevent doc by claim according to xapian db
            match = xdb_query.search(Args.DB_PATH, record['claim'], pagesize=1)[0]

        if l_evidence:
            evidence = concat_evidence(d_titles, title_2_sent_ids)
            if not evidence:
                print(title_2_sent_ids, '\n')
        else:
            doc = json.loads(match[2])
            evidence = " ".join(doc['sentences'].values())

        content = "\t".join([id_, label, record['claim'], evidence])
        fout.write(content + "\n")

    fin.close()
    fout.close()
