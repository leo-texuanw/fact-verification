
import xapian as _x
import json
import os
from contextlib import closing
from tqdm import tqdm
import time


DIR = './wiki-pages-text/'
DATA_FILES = os.listdir(DIR)
# we want our doc to contain title, terms, {sentence -> id}
# 1. We start with a blank title. 
# 2. If we encounter a new title, we add a tuple (sentence, sentence_id)
#    to some empty list. 
# 3. While we keep seeing the same title, we keep appending. 
# 4. When we see a new title, we have to take that list and use it
#    to add a new entry into our db. We take every sentence and combine
#    them to form some text. Then we use the list ot make a dict.
#    Our document object must have title, that dict, and whole text. 
# 5. If there are more lines, then we repeat steps 2-3 with
#    our new title.
def create_full_text(sentence_info):
	""" Takes in a list of [(sentence -> id)] and combines all the 
	strings together to get the full text of a document.
	"""
	return ''.join(map(lambda x: x[0], sentence_info))

def add_new_entry(db, sentence_info, title, docid):
	# make a new document.
	x_doc = _x.Document()

	# setup indexer
	indexer = _x.TermGenerator()
	indexer.set_stemmer(_x.Stem("english"))
	indexer.set_document(x_doc)

	# index terms
	text = create_full_text(sentence_info)
	indexer.index_text(text)

	# store the title, text and sentence_dictionary (id -> sentence)
	# into the data blob
	data_blob = {}
	data_blob['title'] = title
	data_blob['sentences'] = dict(sentence_info)
	x_doc.set_data(json.dumps(data_blob))
	
	#save
	db.replace_document(docid, x_doc)

start = time.time()
current_title = ""
sentence_info = []
curr_docid = 1

# try to make a db in pwd
os.mkdir('./xdb/')

with closing(_x.WritableDatabase('./xdb/test_wiki.db',
                                 _x.DB_CREATE_OR_OPEN)) as x_db:
	# TODO: will need to modify it to go through every text file.
	for data_file in DATA_FILES:
		with open(os.path.join(DIR, data_file), 'r', encoding = "utf-8") as f:
			lines = f.readlines()
			for line in lines:
				title, sentence_id, sentence = line.split(' ', 2)
				if not sentence_id.isdigit():
					continue
				sentence = sentence.strip('\n')

				# if first title, then change current title. 
				if current_title == "":
					current_title = title

				if title != current_title:
					# code that will add new entry into our db.
					add_new_entry(x_db, sentence_info, title, curr_docid)
					curr_docid += 1

					# code that resets some variables for the next document.
					current_title = title
					sentence_info = []

				sentence_info.append((sentence, int(sentence_id)))

		print(data_file, "is complete!")

print("took", time.time() - start, "seconds to finish")