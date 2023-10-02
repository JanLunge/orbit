from flair.data import Corpus
from flair.datasets import ColumnCorpus
from flair.embeddings import WordEmbeddings, FlairEmbeddings, StackedEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

# Define columns
columns = {0: 'text', 1: 'slot'}

# Directory where the data resides
data_folder = './src/intent'

# Load corpus
corpus: Corpus = ColumnCorpus(data_folder, columns,
                              train_file='src/intent/sequence_tags.csv',
                              test_file='src/intent/sequence_tags.csv')

# Make the tag dictionary from the corpus
tag_dictionary = corpus.make_tag_dictionary(tag_type='slot')

# Create embeddings
embedding_types = [WordEmbeddings('glove'), FlairEmbeddings('news-forward'), FlairEmbeddings('news-backward')]
embeddings = StackedEmbeddings(embeddings=embedding_types)

# Initialize sequence tagger (NER)
tagger = SequenceTagger(hidden_size=256, embeddings=embeddings, tag_dictionary=tag_dictionary, tag_type='slot', use_crf=True)

# Train model
trainer = ModelTrainer(tagger, corpus)
trainer.train('./', max_epochs=10)
