# random forests for wsta
from sklearn.ensemble import RandomForestClassifier
import pickle
import time
import sentence_selection_helpers
PARALLEL = True
start = time.time()
if PARALLEL:
	forest = RandomForestClassifier(n_estimators = 10, n_jobs = -1, max_features = None)
else:
	forest = RandomForestClassifier(n_estimators = 10)

filename = 'sentence_forest.sav'
sentence_selection_helpers.train_sklearn_model(forest, filename)


