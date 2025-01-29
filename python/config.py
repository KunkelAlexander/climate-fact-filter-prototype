### **`config.py`**
# Configuration file for Internal Knowledge Database

# Paths
SCRAPING_OUTPUT_DIR           = r"C:\Users\TE\Documents\20250103_tande_publications\html"  # Directory to save fetched HTML files
PUBLICATIONS_DIR              = r"C:\Users\TE\Documents\20250103_tande_publications\pdf"    # Directory to store downloaded PDFs
PUBLICATIONS_METADATA_FILE    = r"C:\Users\TE\Documents\20250103_tande_publications\metadata.csv"    # Directory to store PDF metadata


# Embedding Model
EMBEDDING_MODELS = {
    "all-MiniLM-L6-v2": r"embeddings/20250601_all-MiniLM-L6-v2/",
    "all-mpnet-base-v2": r"embeddings/20250601_all-mpnet-base-v2/"
}

FAISS_INDEX_FILES = {
    "L2":     r"faiss_index_l2.bin",
    "Cosine": r"faiss_index_cosine.bin"
}

METADATA_FILE        = r"metadata.json"          # File to store document metadata
CHUNKS_FILE          = r"chunks"
USE_TEXT_INDEX_FILE  = True
CHUNK_SIZE           = 500                       # Number of words per text chunk - This determines the context size vs granularity trade-off
FAISS_TOP_K          = 5                         # Number of top results to retrieve
SEARCH_RESULT_K      = 5

