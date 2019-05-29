# A Fact Verification System
For a given claim, the system is expected to find all relevant documents in
Wikipedia corpus, find the exact sentence(s) that SUPPORT or REFUTES the
claim, otherwise the claim will be labeled as NOTENOUGHINFO.  

## Dataset
The dataset contains 536 millions documents in all, which has been pre-processed
by the staff of COMP90042 at the University of Melbourne. Each row of the corpus
follows the format [document\_title, sentence\_id, sentence\_content].  

The training set has around 15,000 labeled claims with its supporting or
refusing evidence (document title and sentence id in the doc). For those labeled
as NOTENOUGHINFO the evidence field is empty.  

The development set has 5001 instances with the same format as training set.  

In the test set, there are 14997 claims without label and evidence which should
be filled by our system.  

## Methodologies
### Indexing
We introduced [Xapian](https://xapian.org/) as our search engine, an open source
search engine library written in C++ with bindings to allow use from more than
ten languages including Python.  

### Document Retrieval
For document retrieval, we aim to match the main objects of the claim with
titles. We use a set of hand-crafted **entity linking** rules to aquire these
objects based on [Constituency Parsing model from
AllenNLP](https://demo.allennlp.org/constituency-parsing). For each claim, we
selected the noun phrases from the top level of the returned hierplane tree and
combined with manually generated noun phrases according to sentences' part of
speech tagging to form a candidate set of targets titles $T$. Then we filtered
out those elements in the set $T$ that's not in document title set. All the
remaining noun phrases in $T$ will be passed to the next stage.  

### Sentence Selection
At this stage, We fine tuned a pre-trained model [BERT
Base](https://github.com/google-research/bert) from google research for sentence
selection. We processed all centences of documents in $T$ in a format
[unique\_id, label, claim, sentence], so they can be fit into BERT model and be
classified into two classes RELEVANT or IRRELEVANT. All RELEVANT centences will
be considered as evidence for the final stage.  

### Labeling
Again, we used BERT Base for label prediction. And similar to last stage we
concatenated all evidence of a claim and generate each claim into an example in
the format [unique\_id, constant\_string, claim, concated\_evidence] then fit to
BERT model.  

## Result
This system is very efficent and the whole processes (including indexing, training,
evaluation and predicting) can be finished within 16 hours in any common laptops
with one piece of GPU.  

Finally, we achieved top 20% over more than 100 teams. And the performance are
listed in detail in the below chart:  

| Metrics        | Score  |
| -------------- | ------ |
| Doc Precision  | 74.14% |
| Doc Recall     | 62.24% |
| Doc F1         | 67.67% |
| Sent Precision | 60.76% |
| Sent Recall    | 49.47% |
| Sent F1        | 54.54% |
| Label Accuracy | 54.56% |

## Future Work
Currently, our sentence selection is done independently on each sentence. But
there are many cases where no single sentence contain full information, only
from a combination of several sentences can get the answer. So, maybe we shall
introduce a method that can pop up the spans of the phrases that are relevant to
the claim in the whole document, so that we can choose sentences more accurately
based on the spans.  

And our pipelined method is easy to improve or replace any stage but also
introduce the flaw that errors from last step will influence the performence of
the following steps. A method that integrats two or all steps may improve the
overall performance as well.  
