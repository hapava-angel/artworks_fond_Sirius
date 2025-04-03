from process_data.load_data import load_data  
from embeddings.get_embeddings import get_embeddings
import numpy as np

embeddings_dataset = load_data()

def search(query, k):
    query_embedding = get_embeddings(query)
    query_embedding = np.array(query_embedding).reshape(1, -1)
    scores, retrieved_examples = embeddings_dataset.get_nearest_examples(
        "embeddings", query_embedding,
        k=k
    )
    return scores, retrieved_examples