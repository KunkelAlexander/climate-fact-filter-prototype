

def generate_answer(query, context):
    prompt = f"Context: {context}\n\nQuestion: {query}"
    return query_ollama(prompt)

# Step 4: Retrieve Relevant Chunks
def retrieve(query, index, model, chunks, top_k=2):
    query_embedding = model.encode(query).astype("float32")
    distances, indices = index.search(query_embedding.reshape(1, -1), top_k)
    return [chunks[i] for i in indices[0]]

def retrieve_with_metadata(query, index, model, chunks, metadata, top_k=3):
    query_embedding = model.encode(query).astype("float32")
    distances, indices = index.search(query_embedding.reshape(1, -1), top_k)
    retrieved_chunks = [chunks[i] for i in indices[0]]
    retrieved_metadata = [metadata[i] for i in indices[0]]
    return retrieved_chunks, retrieved_metadata

def truncate_context(context, query, max_tokens=1024):
    # Reserve space for the query and additional prompt text
    reserved_tokens = 300  # Adjust this based on the length of your query
    max_context_tokens = max_tokens - reserved_tokens

    # Truncate context to fit within the limit
    context_tokens = context.split()  # Tokenize the context
    if len(context_tokens) > max_context_tokens:
        context = " ".join(context_tokens[:max_context_tokens])

    return context


def query_ollama(prompt, model="llama3.2", server_url="http://localhost:11435/api/generate"):
    headers = {"Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt}

    response = requests.post(server_url, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")

    # Print and collect the streamed response
    print("Response: ", end="", flush=True)  # Start the response line
    full_response = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            part = data.get("response", "")
            print(part, end="", flush=True)  # Print the response part immediately
            full_response += part
            if data.get("done", False):
                break

    print()  # Finish the response line
    return full_response

def summarize_context(context):
    prompt = f"Summarize the following text:\n\n{context}"
    return query_ollama(prompt)

# Step 1: Extract text from multiple PDFs
def process_multiple_pdfs(folder_path):
    all_chunks = []
    chunk_metadata = []  # Store metadata for each chunk
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            print(f"Processing: {pdf_path}")

            # Extract text from the PDF
            full_text, title = extract_text_from_pdf(pdf_path)

            # Chunk the text
            chunks = list(chunk_text(full_text))
            all_chunks.extend(chunks)

            # Add metadata (file name) for each chunk
            chunk_metadata.extend([{"file_name": filename, "title": "T&E advanced biofuels report (2024)", "page_number": page_number} for page_number, chunk in enumerate(chunks)])

    return all_chunks, chunk_metadata

def generate_answer_with_citation(query, chunks, metadata):
    # Combine chunks into context
    context = "\n\n".join(chunks)


    # Summarize long contexts
    if len(context.split()) > 1500:  # Adjust token threshold as needed
        print("Summarising context ...")
        context = summarize_context(context)


    print("Truncating context ...")
    # Step 5: Generate answer
    truncated_context = truncate_context(context, query, max_tokens=512)

    prompt = f"Context: {context}\n\nQuestion: {truncated_context}"

    print("Querying LLM with prompt: ", prompt)

    # Generate answer using the model
    answer = query_ollama(prompt)

    # Add citations to the answer
    citations = [f"Title: {meta['title']}, Page: {meta['page_number']}" for meta in metadata]
    citation_text = "\n".join(citations)

    return f"{answer}\n\nCitations:\n{citation_text}"

# Small and fast embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Folder containing multiple PDFs
folder_path = r"C:\Users\TE\Documents\fake_news_sharepics\my-cross-platform-app\python\reports"  # Replace with your folder path

# Process all PDFs in the folder
#all_chunks, chunk_metadata = process_multiple_pdfs(folder_path)

# Step 3: Create FAISS index
#index, embeddings = create_faiss_index(all_chunks, embedding_model)

#def check_truth_with_ollama(extracted_text):
#
#
#    # Step 3: Query and retrieve relevant chunks with metadata
#    query = f"Keep your answer very short. Is the statement true or false? {extracted_text}"
#    print("Asking ollama: ", query)
#    retrieved_chunks, retrieved_metadata = retrieve_with_metadata(query, index, embedding_model, all_chunks, chunk_metadata)
#
#    # Step 4: Generate answer with citations
#    answer_with_citation = generate_answer_with_citation(query, retrieved_chunks, retrieved_metadata)
#
#    return answer_with_citation
