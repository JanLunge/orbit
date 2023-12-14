import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
import os


# Function to save embeddings to a file
def save_embeddings(embeddings, file_name):
    with open(file_name, 'wb') as file:
        pickle.dump(embeddings, file)


# Function to load embeddings from a file
def load_embeddings(file_name):
    with open(file_name, 'rb') as file:
        return pickle.load(file)


# Function to check if embeddings file exists
def embeddings_file_exists(file_name):
    return os.path.exists(file_name)


# Embeddings file name
embeddings_file = 'function_embeddings.pkl'

# Prepare your data (list of (ID, function docstring) tuples)

# Separate IDs and docstrings
examples_data = [
    [
        "get_time",
        "what time is it?"
    ],
    [
        "get_date",
        "what day is it?"
    ],
    [
        "set_timer",
        "set a timer for 5 minutes"
    ]
]
# TODO: load functions from functions_examples.json
if os.path.exists("./function_examples.json"):
    with open("./function_examples.json", "r") as f:
        examples_data = json.load(f)
if len(examples_data) > 0:
    function_ids, function_docstrings = zip(*examples_data)

function_docs = []
if os.path.exists("./functions_docs.json"):
    with open("./functions_docs.json", "r") as f:
        function_docs = json.load(f)

# Check if embeddings are already computed and saved
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
# TODO: create a new model every time the functions.json file is changed (md5)
if not embeddings_file_exists(embeddings_file):
    print("Embeddings file not found, computing embeddings...")
    # Embed the Docstrings
    function_embeddings = sentence_model.encode(function_docstrings)

    # Save the embeddings for future use
    save_embeddings(function_embeddings, embeddings_file)
else:
    # Load the embeddings if already computed
    function_embeddings = load_embeddings(embeddings_file)


# Function to find similar functions returns the id of the top k matches
def find_similar_functions(query, k=5):
    # Embed the Query
    query_embedding = sentence_model.encode([query])[0]

    # Compute Cosine Similarities
    similarities = cosine_similarity([query_embedding], function_embeddings)[0]

    # Retrieve Top K matches based on similarities
    top_k_indices = np.argsort(similarities)[::-1][:k]
    return [(function_ids[index],) for index in top_k_indices]

# # Example usage
# query = "can you tell me the time?"
# similar_functions = find_similar_functions(query, k=3)
# for id, docstring in similar_functions:
#     print(f"ID: {id}, Docstring: {docstring}")
