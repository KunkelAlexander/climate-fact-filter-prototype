from PIL import Image, ImageDraw, ImageFont
import pytesseract

# Step 1: Create a test image with some text
def create_test_image():
    # Create a blank white image
    image = Image.new('RGB', (200, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Set a font (use a default if no TTF font is available)
    try:
        font = ImageFont.truetype("arial.ttf", 15)  # or replace with another TTF font path
    except IOError:
        font = ImageFont.load_default()

    # Draw text onto the image
    text = "Hello, Tesseract!"
    draw.text((10, 40), text, fill=(0, 0, 0), font=font)
    return image

# Step 2: Run OCR on the test image
def test_tesseract():
    image = create_test_image()
    extracted_text = pytesseract.image_to_string(image)
    print("Extracted Text:", extracted_text)

# Run the test
if __name__ == "__main__":
    test_tesseract()
