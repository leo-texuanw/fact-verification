import sys
import json

import pandas as pd


if __name__ == '__main__':
    """ Example:
        python probs2labels.py test_results.tsv test_file.json
    """
    f_pred_probs = sys.argv[1]
    f_test = sys.argv[2]
    output_file = "submit_erase2.json"

    probs = pd.read_csv(f_pred_probs, sep='\t', header=None)
    probs.columns = ["SUPPORTS", "REFUTES", "NOT ENOUGH INFO"]

    maxidx = probs.idxmax(axis=1)

    with open(f_test, 'r') as f_result:
        test_data = json.load(f_result)

    # TODO: make it a function, solve step 2 and 3 separately
    output_content, i = {}, 0
    for id_, record in test_data.items():
        record['label'] = maxidx[i]
        if record['label'] == "NOT ENOUGH INFO":
            record['evidence'] = []
        output_content[id_] = record
        i += 1

    with open(output_file, 'w') as f_output:
        f_output.write(json.dumps(output_content))
