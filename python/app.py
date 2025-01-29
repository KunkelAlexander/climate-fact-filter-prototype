from flask import Flask, request, send_file, jsonify, make_response
from flask_cors import CORS
from io import BytesIO
import os
import time
import json
import hashlib
import search_faiss

from PIL import Image, ImageDraw, ImageFont
import pytesseract

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import the separate ChatGPT function
from ai_service import check_truth_with_chatgpt

#######################################################
# 1. Flask & Database Setup
#######################################################

app = Flask(__name__)
CORS(app, expose_headers=["x-description"])

DATABASE_URL = "sqlite:///image_records.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class ImageRecord(Base):
    __tablename__ = 'image_records'
    id = Column(Integer, primary_key=True)
    hash = Column(String, unique=True)
    input_image_path = Column(String)
    output_image_path = Column(String)
    extracted_text = Column(String)
    truthfulness_response = Column(String)

Base.metadata.create_all(engine)

print("System ready! You can now ask questions.")

# -------------------------------------------
# 1A. FAISS Initialization (Important)
# -------------------------------------------
print("Loading the FAISS index...")
faiss_index, embedding_model, all_chunks, metadata, normalise = search_faiss.initialize_search_index(
    model_name="all-mpnet-base-v2",   # or your chosen model
    similarity_metric="L2"           # or "Cosine", etc.
)
ALPHA = 0.05
SELECTED_TYPES = ['Briefing', 'Press Release', 'Unknown Type', 'Report', 'Letter',
       'Opinion', 'News', 'Publication', 'Consultation response', 'Internal', 'Spreadsheet'] # or a list of types if you want to filter
print("FAISS index loaded successfully!")

#######################################################
# 2. Helper Functions
#######################################################

def generate_image_hash(file_bytes: bytes) -> str:
    """Generate a SHA-256 hash of the file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()

def save_input_image(image_bytes: bytes, uploads_folder: str, image_hash: str) -> str:
    """
    Saves the uploaded (input) image bytes to disk as a JPG,
    returns the full file path.
    """
    input_path = os.path.join(uploads_folder, f"{image_hash}_input.jpg")
    # Open from bytes to ensure correct format
    img = Image.open(BytesIO(image_bytes))
    # Convert to RGB if needed
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(input_path, "JPEG")
    return input_path

def retrieve_or_create_record(session, image_hash: str):
    """
    Check if there's an existing record for this hash. If found,
    return that record; otherwise, return None.
    """
    existing_record = session.query(ImageRecord).filter_by(hash=image_hash).first()
    return existing_record

def perform_ocr(image_bytes: bytes) -> str:
    """
    Performs OCR on the given image bytes using pytesseract
    and returns the extracted text.
    """
    img = Image.open(BytesIO(image_bytes))
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    text = pytesseract.image_to_string(img)
    return text

def apply_grayscale_overlay_with_red_crosses(image: Image.Image, alpha=0.5) -> Image.Image:
    """
    Applies a grayscale + white overlay, then draws red crosses.
    """
    grayscale_image = image.convert("L").convert("RGB")
    white_overlay = Image.new("RGB", image.size, color="white")
    overlay_image = Image.blend(image, white_overlay, alpha=alpha)

    draw = ImageDraw.Draw(overlay_image)
    draw.line((0, 0, overlay_image.width, overlay_image.height), fill="red", width=20)
    draw.line((0, overlay_image.height, overlay_image.width, 0), fill="red", width=20)
    return overlay_image

def edit_image_with_logo_and_text(image_bytes: bytes, logo_path: str, is_likely_true: bool) -> Image.Image:
    """
    Applies the red-cross overla if false, attaches a logo in the bottom-right corner,
    and draws the answer text on the image.
    """
    image = Image.open(BytesIO(image_bytes))
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    if not is_likely_true:
        # 1) Apply grayscale overlay with crosses
        edited = apply_grayscale_overlay_with_red_crosses(image, alpha=0.5)

        # 2) Additional big cross lines (optional, you might remove if redundant)
        draw = ImageDraw.Draw(edited)
        draw.line((0, 0, edited.width, edited.height), fill="red", width=20)
        draw.line((0, edited.height, edited.width, 0), fill="red", width=20)
    else:
        edited = image
    # 3) Insert the logo (if it exists)
    #if os.path.exists(logo_path):
    #    logo = Image.open(logo_path).convert("RGBA")
    #    # Example: scale the logo to ~1/3 of the image width
    #    logo_width = edited.width // 3
    #    logo_ratio = logo_width / logo.width
    #    logo_height = int(logo.height * logo_ratio)
    #    logo = logo.resize((logo_width, logo_height))
#
    #    logo_x = edited.width - logo_width
    #    logo_y = edited.height - logo_height
    #    edited.paste(logo, (logo_x, logo_y), logo)

    return edited

def save_output_image(edited_image: Image.Image, uploads_folder: str, image_hash: str) -> str:
    """
    Saves the edited (output) image to disk and returns its file path.
    """
    output_path = os.path.join(uploads_folder, f"{image_hash}_output.jpg")
    edited_image.save(output_path, "JPEG")
    return output_path

def build_flask_image_response(edited_image: Image.Image, text_response: str, is_statement_true: bool):
    """
    Converts the edited PIL image to a BytesIO response and attaches a
    JSON-encoded text response and truthfulness flag in the 'x-description' header.

    Parameters:
    - edited_image (Image.Image): The PIL image to be returned.
    - text_response (str): The response text explaining the truthfulness of the statement.
    - is_statement_true (bool): A boolean flag indicating whether the statement is true or false.

    Returns:
    - Flask response object containing the image and metadata.
    """
    output = BytesIO()
    edited_image.save(output, format='JPEG')
    output.seek(0)

    # Create JSON metadata
    metadata = {
        "text": text_response,
        "is_statement_true": is_statement_true  # ✅ Include truthfulness flag
    }

    response = make_response(send_file(output, mimetype='image/jpeg'))
    response.headers['x-description'] = json.dumps(metadata)

    return response

def create_and_commit_record(session, image_hash, input_path, output_path, extracted_text, truthfulness_response):
    """
    Creates a new ImageRecord and saves it to the database.
    """
    new_record = ImageRecord(
        hash=image_hash,
        input_image_path=input_path,
        output_image_path=output_path,
        extracted_text=extracted_text,
        truthfulness_response=truthfulness_response
    )
    session.add(new_record)
    session.commit()

#######################################################
# 3. Routes
#######################################################

@app.route('/process-image', methods=['POST'])
def process_image():
    """
    Receives an image via POST, performs OCR, queries ChatGPT for truthfulness,
    edits the image, and returns the result.
    """
    session = Session()

    # 1) Read the file and generate a hash
    file = request.files['image']
    file_bytes = file.read()
    image_hash = generate_image_hash(file_bytes)

    # 2) Check if there's an existing record
    existing_record = retrieve_or_create_record(session, image_hash)
    if existing_record and os.path.exists(existing_record.output_image_path):
        # Optional 2-second delay for debugging
        time.sleep(2)

        # Return previously processed image
        with open(existing_record.output_image_path, "rb") as f:
            output = BytesIO(f.read())
        output.seek(0)

        response = make_response(send_file(output, mimetype='image/jpeg'))
        response.headers['x-description'] = json.dumps({"text": existing_record.truthfulness_response})
        session.close()
        return response
    elif existing_record:
        # If record is found but file is missing, remove the record
        session.delete(existing_record)
        session.commit()

    # 3) Save the input image
    uploads_folder = '../uploads'
    input_path = save_input_image(file_bytes, uploads_folder, image_hash)

    # 4) Perform OCR
    extracted_text = perform_ocr(file_bytes)
    print("Extracted text:", extracted_text)

    # 5) Generate answer (via ChatGPT or future local LLM)
    # ---- Pass FAISS objects & params ----
    truthfulness_response = check_truth_with_chatgpt(
        extracted_text=extracted_text,
        faiss_index=faiss_index,           # Global from top-level load
        embedding_model=embedding_model,   # Global from top-level load
        all_chunks=all_chunks,
        metadata=metadata,
        normalise=normalise,
        alpha=ALPHA,
        selected_types=SELECTED_TYPES,
        max_sources=5
    )



    # 6) Edit the image
    logo_path = 'logo.png'
    edited_image = edit_image_with_logo_and_text(file_bytes, logo_path, truthfulness_response["is_likely_true"])

    # 7) Save the output image
    output_path = save_output_image(edited_image, uploads_folder, image_hash)

    # 8) Create DB record
    create_and_commit_record(
        session,
        image_hash,
        input_path,
        output_path,
        extracted_text,
        truthfulness_response["statement_analysis"]
    )

    # 9) Build the Flask response
    response = build_flask_image_response(edited_image, truthfulness_response["statement_analysis"], truthfulness_response["is_likely_true"])
    session.close()
    return response

from flask import send_from_directory

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    uploads_folder = "C:/Users/TE/Documents/20241108_climate_fake_filter/uploads"
    return send_from_directory(uploads_folder, filename)

@app.route('/api/gallery-images', methods=['GET'])
def get_gallery_images():
    """
    Lists existing _input and _output image pairs from a known folder.
    """
    uploads_folder = 'C:/Users/TE/Documents/20241108_climate_fake_filter/uploads'
    images = []

    for filename in os.listdir(uploads_folder):
        if filename.endswith('_input.jpg'):
            base_name = filename.split('_input')[0]
            input_image = os.path.join(uploads_folder, f"{base_name}_input.jpg")
            output_image = os.path.join(uploads_folder, f"{base_name}_output.jpg")
            if os.path.exists(output_image):
                images.append({
                    "input": f"/uploads/{base_name}_input.jpg",
                    "output": f"/uploads/{base_name}_output.jpg"
                })

    return jsonify(images)

if __name__ == '__main__':
    app.run(debug=True)
