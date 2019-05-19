#!/usr/bin/env python
# coding: utf-8

import json
import xapian


def get_query(querystring, prefix=None):

    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

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


def search(dbpath, query, offset=0, pagesize=10):
    """ offset - defines starting point within result set
        pagesize - defines number of records to retrieve
    """

    # Open the database we're going to search.
    db = xapian.Database(dbpath)

    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    # And print out something about each match
    matches = []
    for match in enquire.get_mset(offset, pagesize, None, None):
        fields = json.loads(match.document.get_data())
        # print(fields)
        print("{rank:} #{docid:3d} {title:}\n {sentences:} \n".format(
            rank=match.rank + 1,
            docid=match.docid,
            title=fields.get('title', ''),
            sentences=fields.get('sentences', ''),
            ))
        matches.append(match.docid)

    # Finally, make sure we log the query and displayed results
    # support.log_matches(querystring, offset, pagesize, matches)


if __name__ == '__main__':
    DB_PATH = './xdb/wiki.db'
    prefix = 'text'  # options: ['title', 'text', None]
    querystring = "Kevin Kraus"
    query = get_query(querystring, prefix)
    search(DB_PATH, query)
