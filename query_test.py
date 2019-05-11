import xapian as _x

qp = _x.QueryParser()
qp.set_stemmer(_x.Stem('english'))
qp.set_db(_x.Database('./xdb/movies.db'))
qp.set_stemming_strategy(_x.QueryParser.STEM_SOME)
query = parse_query('doc')

enq = _x.Enquire(x_db)
enq.set_query(query)

for res in enq.get_mset(0, x_db.get_doccount(), None, None):
	print(res.document.get_data())