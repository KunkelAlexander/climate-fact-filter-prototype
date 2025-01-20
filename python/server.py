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

from openai import OpenAI
client = OpenAI()

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



print("System ready! You can now ask questions.")


def check_truth_with_chatgpt(extracted_text):
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
    input_image_path = f"../uploads/{image_hash}_input.jpg"
    output_image_path = f"../uploads/{image_hash}_output.jpg"
    image.save(input_image_path, "JPEG")

    # Perform OCR on the image to extract text
    extracted_text = pytesseract.image_to_string(image)
    print("Extracted Text:", extracted_text)  # Debugging print

    # Call OpenAI API to check if the text is true or false
    truthfulness_response = check_truth_with_chatgpt(extracted_text)
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
    logo = Image.open(r'logo.png').convert("RGBA")

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
