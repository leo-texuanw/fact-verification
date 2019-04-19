import json
import sys

NEI = 'NOT ENOUGH INFO'

actual = json.load(open(sys.argv[1]))
predicted = json.load(open(sys.argv[2]))

assert set(actual.keys()) == set(predicted.keys())

correct_label = num_instances = 0
evidence_prec = num_eprec = 0
evidence_recall = num_erec = 0
doc_prec = num_dprec = 0
doc_rec = num_drec = 0

for ident, arecord in actual.items():
	precord = predicted[ident]

	alabel = arecord['label'].upper()
	plabel = precord['label'].upper()
	if alabel == plabel:
		correct_label += 1
	num_instances += 1

	if alabel != NEI:
		prec = prec_hits = 0
		rec = rec_hits = 0

		aes = arecord['evidence']
		pes = precord['evidence'][:5]
		for pe in pes:
			if pe in aes:
				prec += 1
			prec_hits += 1

		for ae in aes:
			if ae in pes:
				rec += 1
			rec_hits += 1

		ads = set(map(lambda ds: ds[0], aes))
		last_pd = None
		dp = ndp = 0
		for pe in pes:
			if not last_pd or pe[0] != last_pd:
				if pe[0] in ads:
					dp += 1
				ndp += 1
			last_pd = pe[0]

		pds = set(map(lambda ds: ds[0], pes))
		dr = ndr = 0
		for ae in ads:
			if ae in pds:
				dr += 1
			ndr += 1

		if prec_hits > 0:
			evidence_prec += float(prec) / prec_hits
			num_eprec += 1

		if ndp > 0:
			doc_prec += float(dp) / ndp
			num_dprec += 1

		assert rec_hits > 0
		evidence_recall += float(rec) / rec_hits
		num_erec += 1

		assert ndr > 0
		doc_rec += float(dr) / ndr
		num_drec += 1


accuracy = correct_label / float(num_instances)
print('Label Accuracy', '\t\t%.2f%%' % (100 * accuracy))

precision = evidence_prec / float(num_eprec) if num_eprec != 0 else 0
recall = evidence_recall / float(num_erec) if num_erec != 0 else 0
f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
print('Sentence Precision', '\t%.2f%%' % (100 * precision))
print('Sentence Recall', '\t%.2f%%' % (100 * recall))
print('Sentence F1', '\t\t%.2f%%' % (100 * f1))

doc_precision = doc_prec / float(num_dprec) if num_dprec != 0 else 0
doc_recall = doc_rec / float(num_drec) if num_drec != 0 else 0
doc_f1 = 2 * doc_precision * doc_recall / (doc_precision + doc_recall) if doc_precision + doc_recall > 0 else 0
print('Document Precision', '\t%.2f%%' % (100 * doc_precision))
print('Document Recall', '\t%.2f%%' % (100 * doc_recall))
print('Document F1', '\t\t%.2f%%' % (100 * doc_f1))

		


