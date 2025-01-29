import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime
import faiss
import config


# Load FAISS index, metadata, and chunks
def load_faiss_index(index_file, metadata_file, chunk_file):

    print(f"Loading FAISS index ({index_file}), metadata ({metadata_file}), and chunks ({chunk_file})...")

    if not os.path.exists(index_file) or not os.path.exists(metadata_file) or not os.path.exists(chunk_file):
        raise ValueError("No FAISS index available. Please create it using embeddings/build_faiss.py")

    index = faiss.read_index(index_file)
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    with open(chunk_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    return index, metadata, chunks


# Initialize the FAISS index (build or load)
def initialize_search_index(model_name, similarity_metric):
    print(f"Using embedding model {model_name}")
    embedding_model = SentenceTransformer(model_name)
    directory  = config.EMBEDDING_MODELS[model_name]
    faiss_path = os.path.join(directory, config.FAISS_INDEX_FILES[similarity_metric])
    meta_path  = os.path.join(directory, config.METADATA_FILE)
    chunk_path = os.path.join(directory, config.CHUNKS_FILE)

    faiss_index, metadata_list, chunks = load_faiss_index(faiss_path, meta_path, chunk_path)

    return faiss_index, embedding_model, chunks, metadata_list, similarity_metric != "L2"

# Perform semantic search
def search_pdfs(query, index, model, chunks, metadata, normalise = False, alpha=0.00, publication_types=None):
    """
    Perform a semantic search with date-based weighting on results.

    Parameters:
        query (str): The search query.
        index (faiss.Index): The FAISS search index.
        model: The embedding model.
        chunks (list): List of text chunks.
        metadata (list): List of metadata for each chunk.
        normalise (bool): Whether to normalise query embeddings.
        alpha (float): Decay factor for date weighting.

    Returns:
        list: A list of search results with date-weighted scoring.
    """
    query_embedding = model.encode(query).astype("float32").reshape(1, -1)

    # Debug dimension mismatch in search_pdfs
    if normalise:
        faiss.normalize_L2(query_embedding)

    # Filter IDs based on metadata
    filtered_ids = [
        idx for idx, meta in enumerate(metadata)
        if meta.get("Publication Type", "Unknown Type") in publication_types
    ]

    # Return no results for empty selection
    if not filtered_ids:
        return []

    # Create IDSelector for filtering
    id_selector = faiss.IDSelectorArray(filtered_ids)

    print(f"Performing search with IDSelector...")
    distances, indices = index.search(query_embedding, config.FAISS_TOP_K, params=faiss.SearchParametersIVF(sel=id_selector))

    # Prepare the results with metadata and date weighting
    results = []
    current_date = datetime.now()

    for i, distance in zip(indices[0], distances[0]):
        if i < len(chunks):  # Ensure the index is within bounds
            metadata_entry = metadata[i]  # Get metadata for the chunk

            # Extract publication date
            publication_date_str = metadata_entry.get("Publication Date", "Unknown Date")
            publication_date = datetime.strptime(publication_date_str, "%b %d, %Y, %I:%M:%S %p")
            days_since_pub = (current_date - publication_date).days

            # Calculate date weight using exponential decay
            date_weight = np.exp(-alpha * days_since_pub/365)

            # Combine similarity distance (lower is better) and date weight
            similarity_score = 1 / (1 + distance)  # Convert FAISS distance to a similarity score
            weighted_score = similarity_score * date_weight

            results.append({
                "filename": metadata_entry.get("PDF URL", "No PDF URL").split('/')[-1],
                "title": metadata_entry.get("Title", "Unknown Title"),
                "summary": metadata_entry.get("Summary", "No Summary"),
                "publication_date": publication_date.strftime("%B %d, %Y"),
                "publication_type": metadata_entry.get("Publication Type", "Unknown Type"),
                "url": metadata_entry.get("Article URL", "No URL"),
                "pdf_url": metadata_entry.get("PDF URL", "No PDF URL"),
                "snippet": chunks[i][:500].replace("\n", " "),  # Add a snippet from the chunk
                "score": similarity_score,
                "date_weight": date_weight,
                "weighted_score": weighted_score,
            })

    # Sort results by weighted score in descending order
    results = sorted(results, key=lambda x: x['weighted_score'], reverse=True)[:config.SEARCH_RESULT_K]

    return results
