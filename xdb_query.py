#!/usr/bin/env python
# coding: utf-8

import json
import xapian


def _get_query(querystring, prefix=None):

    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

    query = None
    if not prefix:
        query = queryparser.parse_query(querystring)
    elif prefix.lower() == "title":
        query = queryparser.parse_query(querystring, 0, 'S')
    elif prefix.lower() == 'text':
        query = queryparser.parse_query(querystring, 0, 'XT')
    else:
        print("WARNING:", prefix, "not match!")
        query = queryparser.parse_query(querystring)

    return query


def search(db_path, query_str, prefix=None, offset=0, pagesize=5):
    """ offset - defines starting point within result set
        pagesize - defines number of records to retrieve
    """

    # Open the database we're going to search.
    db = xapian.Database(db_path)

    # get query
    query = _get_query(query_str, prefix)

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
        print("Rank: {rank:}\t Doc ID: #{docid:3d}\t Title: {title:}\n {sentences:} \n".format(
            rank=rank,
            docid=doc_id,
            title=fields.get('title', ''),
            sentences=fields.get('sentences', ''),
        ))


if __name__ == '__main__':
    DB_PATH = './xdb/wiki.db'
    prefix = 'title'  # options: ['title', 'text', None]
    query_str = "Kevin Kraus"
    matches = search(DB_PATH, query_str, prefix)

    print_matches(matches)
