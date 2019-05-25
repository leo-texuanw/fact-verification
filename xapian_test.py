"""
1. We will use Xapian to create a database of index integer -> some fields. 
2. For now, our two fields are title and terms in a document
3. Create an indexer using xapian.TermGenerator(), create a _x.Document() 
   object, then pass it as argument to the indexer. 
4. You can then supply this indexer some text. 
5. When you are done feeding the indexer, you can pass the document object in that indexer to 
   a database object, using replace. It will then insert this document.
"""


"""
indexing terms:
text: "Green tea ice cream"
terms: ['green', 'tea', 'ice', 'cream']
terms are in lower case
also stores term frequency and positional information.

Stemming reduces inflected or derived words to their root.
Example: connect
matches: connected, connections etc. 
In Xapian: Zconnect
"""

import xapian as _x
import json
s1 = "After young Riley is uprooted from her Midwest life"
t1 = "Insider Out"

# setup an indexer with english stemming.
# Create a document to 
indexer = _x.TermGenerator()
indexer.set_stemmer(_x.Stem("english"))
x_doc = _x.Document()
indexer.set_document(x_doc)

# index unstructured text
# Xapian will parse this and generate a list of terms. 
indexer.index_text(s1)

# index text with prefix: title
indexer.index_text(t1, 1, "S")

# save data to document
x_doc.set_data(json.*s(data, encoding = 'utf8'))
# write into xapian database
# works like a default dictionary, if there is an existing document with that id, 
# it will update, otherwise it will insert. 
x_db.replace_document(rank, x_doc)

print("Code finished running")