# tests/test_helpers.py

import os
import pytest
from PIL import Image
from io import BytesIO

from ..app import (
    generate_image_hash,
    perform_ocr,
    apply_grayscale_overlay_with_red_crosses,
    edit_image_with_logo_and_text,
    # etc. ... other helpers you want to test
)

@pytest.fixture
def sample_image_bytes():
    """Creates an in-memory JPEG image to use for testing."""
    img = Image.new('RGB', (100, 100), color='blue')  # a simple blue square
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.read()

def test_generate_image_hash(sample_image_bytes):
    """Tests that generate_image_hash returns a non-empty string."""
    hash_value = generate_image_hash(sample_image_bytes)
    assert isinstance(hash_value, str)
    assert len(hash_value) > 0

def test_perform_ocr(sample_image_bytes):
    """
    Tests the perform_ocr function. Since our sample image is just a blue square
    with no text, we expect an empty string or minimal OCR garbage.
    """
    text = perform_ocr(sample_image_bytes)
    # Typically an empty image might return "" or some random characters
    assert isinstance(text, str)

def test_apply_grayscale_overlay_with_red_crosses(sample_image_bytes):
    """Ensures the function returns a PIL Image of the same size."""
    img = Image.open(BytesIO(sample_image_bytes))
    output_img = apply_grayscale_overlay_with_red_crosses(img, alpha=0.5)
    assert output_img.size == img.size
    assert isinstance(output_img, Image.Image)

def test_edit_image_with_logo_and_text(sample_image_bytes, tmp_path):
    """
    Tests the image editing function with a dummy 'logo.png'.
    We'll create a small placeholder logo file in a temp directory.
    """
    # Create a small red logo in a temp directory
    logo_path = os.path.join(tmp_path, "logo.png")
    logo_img = Image.new('RGBA', (20, 20), color='red')
    logo_img.save(logo_path)

    edited_img = edit_image_with_logo_and_text(
        sample_image_bytes,
        logo_path,
        "Test Overlay"
    )
    assert isinstance(edited_img, Image.Image)
    assert edited_img.size == (100, 100)  # same as sample_image_bytes
