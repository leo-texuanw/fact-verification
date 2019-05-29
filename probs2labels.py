# This file is for translating bert output 'test_result.tsv' to
# actually data file.

# Example for labeling:
#   $ python probs2labels.py test_results.tsv test_file.json

# Example for sentence selection result:
#   $ python probs2labels.py sent_test_results.tsv my_test4sent.json \
#       my_test4sent.tsv

import sys
import json

import pandas as pd
from tqdm import tqdm


def labels(test_data, maxidx):
    """ write labels back to dev/test data. """
    output_content, i = {}, 0

    for id_, record in test_data.items():
        record['label'] = maxidx[i]
        if record['label'] == "NOT ENOUGH INFO":
            record['evidence'] = []
        output_content[id_] = record
        i += 1

    return output_content


def sents(test_data, all_sents, maxidx):
    """ write sentence selection result back to dev/test data. """
    # last three digits represent sentence id, so ignore
    evidence, last_id = [], all_sents['id'].iloc[0] // 1000

    i = 0
    for label in tqdm(maxidx):
        id_, title, sent_id = all_sents[['id', 'title', 'sent_id']].iloc[i]
        # get title id from id_, by eliminating sentence id
        cur_id = id_ // 1000

        if cur_id == last_id:
            # belong to the same claim as last row
            if label == 'yes':
                evidence.append([title, int(sent_id)])
        else:
            # archive evidence when jump to next claim
            if evidence:
                test_data[str(last_id)]['evidence'] = evidence
                evidence = []
            elif label == 'yes':
                evidence = [[title, int(sent_id)]]
            last_id = cur_id

        i += 1

    if evidence:
        test_data[str(last_id)]['evidence'] = evidence

    return test_data


if __name__ == '__main__':
    """ Example:
    """
    f_pred_probs = sys.argv[1]
    f_test = sys.argv[2]
    output_file = "testset_after_bert_labelling.json"

    # CHANGE THIS FLAG for task sent as `False`
    FOR_LABLE = True  # specify this run is for result from labeling or not

    probs = pd.read_csv(f_pred_probs, sep='\t', header=None)

    with open(f_test, 'r') as f_result:
        test_data = json.load(f_result)

    if FOR_LABLE:
        # set columns names as labels
        probs.columns = ["SUPPORTS", "REFUTES", "NOT ENOUGH INFO"]
        maxidx = probs.idxmax(axis=1)

        output_content = labels(test_data, maxidx)
    else:
        # set columns names: means current sentence is relevent to claim or not
        probs.columns = ["yes", "no"]
        maxidx = probs.idxmax(axis=1)

        all_sents = pd.read_csv(sys.argv[3], sep='\t', header=None)
        all_sents.columns = ['id', 'label', 'claim', 'evidence', 'title', 'sent_id']

        output_content = sents(test_data, all_sents, maxidx)

    print("start writing back to output_file...")
    with open(output_file, 'w') as f_output:
        f_output.write(json.dumps(output_content))
