# folders
mkdir objects
mkdir runing_output

# dependencies
sudo apt-get install python-xapian
sudo apt-get install libxapian-dev
python -m spacy download en_core_web_lg

# BERT
git clone https://github.com/google-research/bert.git
cd bert && mkdir pre_trained_models
cd pre_trained_models
wget https://storage.googleapis.com/bert_models/2018_10_18/uncased_L-12_H-768_A-12.zip
unzip ncased_L-12_H-768_A-12.zip
