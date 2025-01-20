from flask import Flask, request, send_file, jsonify, make_response
from flask_cors import CORS  # Import CORS
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import pytesseract  # Import pytesseract for OCR
import time
import json
import os

import os
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
import numpy as np
import requests

#from openai import OpenAI

import hashlib
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
CORS(app, expose_headers=["x-description"])  # Allow custom header in the response


# Configure the database (SQLite for simplicity)
DATABASE_URL = "sqlite:///image_records.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# Define the database table
class ImageRecord(Base):
    __tablename__ = 'image_records'
    id = Column(Integer, primary_key=True)
    hash = Column(String, unique=True)
    input_image_path = Column(String)
    output_image_path = Column(String)
    extracted_text = Column(String)
    truthfulness_response = Column(String)

Base.metadata.create_all(engine)  # Create tables



# Initialize the OpenAI client
#client = OpenAI(api_key="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")


# Step 1: Extract Text from PDF
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    title = reader.metadata.get('/Title', None)  # Extract the title from metadata
    title = title if title else "Unknown Title"
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text, title

# Step 2: Chunk Text
def chunk_text(text, chunk_size=250):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

# Step 3: Create Embeddings and FAISS Index
def create_faiss_index(chunks, model):
    embeddings = [model.encode(chunk) for chunk in chunks]
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return index, embeddings


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
all_chunks, chunk_metadata = process_multiple_pdfs(folder_path)

# Step 3: Create FAISS index
index, embeddings = create_faiss_index(all_chunks, embedding_model)


print("System ready! You can now ask questions.")


def check_truth_with_ollama(extracted_text):


    # Step 3: Query and retrieve relevant chunks with metadata
    query = f"Keep your answer very short. Is the statement true or false? {extracted_text}"
    print("Asking ollama: ", query)
    retrieved_chunks, retrieved_metadata = retrieve_with_metadata(query, index, embedding_model, all_chunks, chunk_metadata)

    # Step 4: Generate answer with citations
    answer_with_citation = generate_answer_with_citation(query, retrieved_chunks, retrieved_metadata)

    return answer_with_citation

def check_truth_with_chatgpt(extracted_text):

    file_path = r'C:\Users\TE\Documents\fake_news_sharepics\python\text.txt'  # Replace with the correct path

    # Reading the file content into a string
    with open(file_path, 'r', encoding='utf-8') as file:
        carbon_brief_text = file.read()

    # Create a prompt to send to OpenAI's API
    prompt = f"Is this a true or false about global warming? If it is false, please rewrite the key false statement as a truthful statement. {extracted_text}"

    try:
        # Use the chat.completions.create method
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Use the appropriate model name, e.g., "gpt-4"
            messages=[
                {"role": "system", "content": "Keep your answer very short."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,  # Limit the response length
            temperature=0.7
        )
        # Extract and return the response
        chatgpt_answer = completion.choices[0].message.content
        return chatgpt_answer
    except Exception as e:
        print("Error calling OpenAI API:", e)
        return "Unable to determine truthfulness due to an API error."


def apply_grayscale_overlay_with_red_crosses(image, alpha=0.5):
    # Step 1: Create a grayscale version of the original image
    grayscale_image = image.convert("L").convert("RGB")  # Convert to grayscale, then back to RGB
    white_overlay = Image.new("RGB", image.size, color="white")
    # Step 2: Blend the grayscale image with the original for a grayscale overlay effect
    overlay_image = Image.blend(image, white_overlay, alpha=alpha)  # Adjust alpha as needed for intensity

    # Step 3: Draw red crosses on the blended image
    draw = ImageDraw.Draw(overlay_image)
    draw.line((0, 0, overlay_image.width, overlay_image.height), fill="red", width=20)
    draw.line((0, overlay_image.height, overlay_image.width, 0), fill="red", width=20)

    return overlay_image

@app.route('/process-image', methods=['POST'])
def process_image():

    # Initialize a database session
    session = Session()

    # Retrieve the image file from the request
    file = request.files['image']
    image = Image.open(file)

    # Convert to RGB if the image has an alpha channel
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    # Generate a unique hash for the image
    image_hash = hashlib.sha256(file.read()).hexdigest()

    # Check if the image has already been processed
    existing_record = session.query(ImageRecord).filter_by(hash=image_hash).first()
    if existing_record:
        # Check if the output image file exists
        if os.path.exists(existing_record.output_image_path):

            # Optional 2-second delay for debugging
            time.sleep(2)

            # File exists, return the stored response with the image and text response
            output = BytesIO()
            with open(existing_record.output_image_path, "rb") as img_file:
                output.write(img_file.read())
            output.seek(0)
#
            response = make_response(send_file(output, mimetype='image/jpeg'))
            response.headers['x-description'] = json.dumps({"text": existing_record.truthfulness_response})
            session.close()
            return response
        else:
            # File does not exist, delete the record from the database
            session.delete(existing_record)
            session.commit()


    # Save the input and output images
    input_image_path = f"my-cross-platform-app/uploads/{image_hash}_input.jpg"
    output_image_path = f"my-cross-platform-app/uploads/{image_hash}_output.jpg"
    image.save(input_image_path, "JPEG")

    # Perform OCR on the image to extract text
    extracted_text = pytesseract.image_to_string(image)
    print("Extracted Text:", extracted_text)  # Debugging print

    # Call OpenAI API to check if the text is true or false
    truthfulness_response = check_truth_with_ollama(extracted_text)
    print("ChatGPT Response:", truthfulness_response)  # Debugging print

    negated_response = truthfulness_response

    # Load a comic-style font
    try:
        font = ImageFont.truetype("ComicSansMS.ttf", 24)  # Adjust font size as needed
    except IOError:
        font = ImageFont.load_default(24)


    # Draw the "FAKE" text overlay
    draw = ImageDraw.Draw(image)

    # Calculate text width and height using textbbox
    bbox = draw.textbbox((0, 0), negated_response, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Calculate position to center the text
    x = (image.width - text_width) // 3
    y = 9* (image.height - text_height) // 10
    print(image.width, image.height, x, y)

    image = apply_grayscale_overlay_with_red_crosses(image, 0.5)
    #draw.text((x, y), text, font=font, fill="red")

    # Draw a large red cross over the entire image
    draw.line((0, 0, image.width, image.height), fill="red", width=20)
    draw.line((0, image.height, image.width, 0), fill="red", width=20)

    #draw.text((x, y),negated_response,(255,255,255),font=font)


    # Load the logo (seal.png)
    logo = Image.open(r'C:\Users\TE\Documents\fake_news_sharepics\python\logo.png').convert("RGBA")

    # Scale the logo to be small (e.g., 10% of the image width)
    logo_width = 1 * image.width // 3
    logo_ratio = logo_width / logo.width
    logo_height = int(logo.height * logo_ratio)
    logo = logo.resize((logo_width, logo_height))

    # Position the logo in the bottom-right corner with a small margin
    logo_x = image.width - logo_width  # 20-pixel margin from the edge
    logo_y = image.height - logo_height

    # Paste the logo onto the image with transparency
    image.paste(logo, (logo_x, logo_y), logo)


    # Save the modified image to a BytesIO object
    output = BytesIO()
    image.save(output, format='JPEG')
    output.seek(0)

    # Create text response
    text_response = {
        "text": truthfulness_response
    }

    # Create response with image and text
    response = make_response(send_file(output, mimetype='image/jpeg'))
    response.headers['x-description'] = json.dumps(text_response)


    # Store record in the database
    image_record = ImageRecord(
        hash=image_hash,
        input_image_path=input_image_path,
        output_image_path=output_image_path,
        extracted_text=extracted_text,
        truthfulness_response=truthfulness_response
    )
    session.add(image_record)
    session.commit()  # Save the data


    image.save(output_image_path, "JPEG")


    return response



@app.route('/api/gallery-images', methods=['GET'])
def get_gallery_images():
    uploads_folder = 'C:/Users/TE/Documents/fake_news_sharepics/uploads'
    images = []

    # Get all files in the uploads folder
    for filename in os.listdir(uploads_folder):
        if filename.endswith('_input.jpg'):
            # Get the base name (without _input or _output)
            base_name = filename.split('_input')[0]
            input_image = os.path.join(uploads_folder, f"{base_name}_input.jpg")
            output_image = os.path.join(uploads_folder, f"{base_name}_output.jpg")

            # Check if both input and output images exist
            if os.path.exists(output_image):
                images.append({
                    "input": f"/uploads/{base_name}_input.jpg",
                    "output": f"/uploads/{base_name}_output.jpg"
                })

    return jsonify(images)

if __name__ == '__main__':
    app.run(debug=True)
