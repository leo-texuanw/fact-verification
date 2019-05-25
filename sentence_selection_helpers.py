import pickle
import time

def create_training_data():
    pass # TODO: use to create X,Y for next function.


def train_sklearn_model(clf, filename):
    """ can put any sklearn model here to train for sentence selection"""
    start = time.time()
    X = 1 # TODO: pass the training_data shape: (n_samples, 600) here.
    Y = 2 # TODO: pass the labels, shape: (n_samples, 1) here. 
    clf.fit(X,Y)
    print("training passed")

    # after training is done, save to disk
    pickle.dump(clf, open(filename, 'wb'), protocol = pickle.HIGHEST_PROTOCOL)
    print("training", filename, "took", time.time() - start, "seconds")
    return



def create_dev_data():
    pass # TODO: use to create X,Y for next function


def testing_sklearn_model(model):
    learned_labels = []
    
    # TODO: 
    X = 1 # pass the dev_features here, shape (n_dev, 600) TODO 
    Y = 2 # pass the dev lbaels here, shape (n_dev, 1). TODO
    learned_labels = model.predict(X)
    correct = 0 
    for i,label in enumerate(learned_label):
        if label == Y[i]:
            correct += 1
    total = i + 1
    print("correctness:", correct/total, "%. Well done!")
    return
