#!/usr/bin/env python
# coding: utf-8

# Functions about xapian, for searching and write down all documents titles

import json
from os.path import join

import xapian
from constants import Args


def get_document(db_path, docid):
    """ to use the returned doc do: doc.get_data() """

    db = xapian.Database(db_path)
    return db.get_document(docid)


def get_doc_by_title(db_path, title):
    matches = search(db_path, title, prefix='title')

    for _rank, doc_id, match in matches:
        doc = json.loads(match)
        if doc.get('title', '') == title:
            return doc

    return ""


def save_titles_dict(db_path, output_titles):
    """ save all documents in db into `output_titles`
        with format: docid\ttitle
    """

    titles = {}
    db = xapian.Database(db_path)

    with open(output_titles, 'w') as titles_file:

        postlist = db.postlist("")
        while True:
            try:
                item = next(postlist)  # next(pos, None)
            except StopIteration:
                print(item.docid)
                break
            else:
                doc = db.get_document(item.docid).get_data()
                title = json.loads(doc).get('title', "")
                titles[title] = item.docid
                titles_file.write("{}\t{}\n".format(item.docid, title))

    return titles


# def title_without_parentheses(title):
#     return re.sub('-LRB-.*RRB-', '', title).strip('_')


def load_xapian_titles(path, f_title):
    """ load saved titles as a dictionary """

    titles = {}

    with open(join(path, f_title), 'r') as f:
        for line in f:
            doc_id, title = line.strip('\n').split('\t')
            titles[title] = int(doc_id)
    print("the number of titles:", len(titles))

    # without_parentheses = {}
    # for title, tid in titles.items():
    #     tit = title_without_parentheses(title)
    #     if title != tit:
    #         without_parentheses[tit] = tid

    # titles.update(without_parentheses)

    # print("get new processed titles without parentheses:",
    #       len(without_parentheses))
    # print("after adding titles without parentheses:", len(titles))

    return titles


def _gen_query(querystring, prefix=None):
    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

    query = None
    if not prefix:
        query = queryparser.parse_query(querystring)
    elif prefix.lower() == "title":
        query = queryparser.parse_query(querystring, 0, 'XS')
    elif prefix.lower() == "title_tokens":
        query = queryparser.parse_query(querystring, 0, 'S')
    elif prefix.lower() == 'text':
        query = queryparser.parse_query(querystring, 0, 'XT')
    else:
        print("[WARNING]:", prefix, "not match!")
        query = queryparser.parse_query(querystring)

    return query


def search(db_path, query_str, prefix=None, offset=0, pagesize=5):
    """ offset - defines starting point within result set
        pagesize - defines number of records to retrieve
    """

    # Open the database we're going to search.
    db = xapian.Database(db_path)

    # get query
    query = _gen_query(query_str, prefix)

    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    # And print out something about each match
    matches = []
    for match in enquire.get_mset(offset, pagesize, None, None):
        doc = match.document.get_data()
        matches.append((match.rank+1, match.docid, doc))

    return matches


def print_matches(matches):
    for rank, doc_id, match in matches:
        fields = json.loads(match)
        print("Rank: {rank:}\t Docid: {doc_id:} \t Title: {title:} \n {sentences:} \n".format(
            rank=rank,
            doc_id=doc_id,
            title=fields.get('title', ''),
            sentences=fields.get('sentences', ''),
        ))


if __name__ == '__main__':
    OUTPUT_TITLES = join(Args.OBJECTS, Args.TITLES)

    prefix = 'title_tokens'  # options: ['title', 'title_tokens', 'text', None]
    query_str = "Kevin Kraus"  # Selina

    matches = search(Args.DB_PATH, query_str, prefix)
    print_matches(matches)
    # titles = save_titles_dict(Args.DB_PATH, OUTPUT_TITLES)

    # print(get_document(Args.DB_PATH, 104543))

    title = 'Damon_Albarn'
    print(get_doc_by_title(Args.DB_PATH, title))
