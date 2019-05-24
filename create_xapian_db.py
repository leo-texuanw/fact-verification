"""
 we want our doc to contain title, terms, {sentence_id -> sentence}
 1. We start with a blank title.
 2. If we encounter a new title, we add a tuple (sentence_id, sentence)
    to some empty list.
 3. While we keep seeing the same title, we keep appending.
 4. When we see a new title, we have to take that list and use it
    to add a new entry into our db. We take every sentence and combine
    them to form some text. Then we use the list to make a dict.
    Our document object must have title, that dict, and whole text.
 5. If there are more lines, then we repeat steps 2-3 with
    our new title.
"""

import errno
import json
import os
from os.path import join
from time import time

from contextlib import closing
import xapian
from tqdm import tqdm


def create_full_text(sentence_info):
    """ Takes in a list of [(id -> sentence)] and combines all the
    strings together to get the full text of a document.
    """
    return ' '.join(map(lambda x: x[1], sentence_info))


def add_new_entry(db, sentence_info, title, docid):
    title_tokens = title.replace('_', ' ')

    # make a new document.
    x_doc = xapian.Document()

    # setup indexer
    indexer = xapian.TermGenerator()
    indexer.set_stemmer(xapian.Stem("english"))
    indexer.set_document(x_doc)

    # Index each field with a suitable prefix.
    text = create_full_text(sentence_info)
    indexer.index_text(title_tokens, 1, 'S')
    indexer.index_text(title, 1, 'XS')
    indexer.index_text(text, 1, 'XT')

    # index terms
    indexer.index_text(title_tokens)
    indexer.increase_termpos()
    indexer.index_text(text)

    # store the title, text and sentence_dictionary (id -> sentence)
    # into the data blob
    data_blob = {}
    data_blob['title'] = title
    data_blob['sentences'] = dict(sentence_info)
    x_doc.set_data(json.dumps(data_blob))
    x_doc.add_boolean_term(title)

    # save
    db.replace_document(docid, x_doc)


def save_2_db(x_db, dir_, data_file, curr_docid):
    with open(join(dir_, data_file), 'r', encoding="utf-8") as f:
        lines = f.readlines()

        sentence_info = []
        current_title = title = lines[0].strip('\n').split(' ', 1)[0]
        for line in lines:
            title, sentence_id, sentence = line.strip('\n').split(' ', 2)

            if title != current_title:
                # code that will add new entry into our db.
                add_new_entry(x_db, sentence_info, title, curr_docid)

                # code that resets some variables for the next document.
                curr_docid += 1
                current_title = title
                sentence_info = []

            try:
                sentence_info.append((int(sentence_id), sentence))
            except (TypeError, ValueError):
                continue

        if sentence_info:
            add_new_entry(x_db, sentence_info, title, curr_docid)
            curr_docid += 1

    print(data_file, "is complete!")
    return curr_docid


if __name__ == '__main__':
    CORPUS_DIR = './wiki-pages-text/'
    DATA_FILES = os.listdir(CORPUS_DIR)
    DB_PATH = './xdb/'
    DB_NAME = 'wiki.db'

    # try to make a db in pwd
    try:
        os.mkdir(DB_PATH)
        print("create dir", DB_PATH)
    except (OSError, IOError) as e:
        if e.errno != errno.EEXIST:
            raise

    START = time()
    with closing(xapian.WritableDatabase(
            join(DB_PATH, DB_NAME),
            xapian.DB_CREATE_OR_OPEN)
    ) as x_db:

        curr_docid = 1
        for data_file in tqdm(DATA_FILES):
            if not data_file.endswith('.txt'):
                continue
            curr_docid = save_2_db(x_db, CORPUS_DIR, data_file, curr_docid)

    print("took", time() - START, "seconds to finish")
