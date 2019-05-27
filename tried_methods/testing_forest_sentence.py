import sentence_selection_helpers
import pickle
import time

start = time.time()
filename = 'sentence_forest.sav'
loaded_model = pickle.load(open(filename, 'rb'))

sentence_selection_helpers.testing_sklearn_model(loaded_model)

print("took us", time.time() - start, "seconds to complete this")
print("yay, one step closer to becoming a machine learning expert!	")