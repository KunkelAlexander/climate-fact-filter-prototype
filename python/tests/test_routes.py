# tests/test_routes.py

import pytest
from io import BytesIO
from PIL import Image
from ..app import app, Base, engine

@pytest.fixture(scope="module")
def test_client():
    """
    A Pytest fixture that creates a Flask test client.
    Also sets up or clears the test database before/after tests if needed.
    """
    # Optionally, you could point to a different DB (e.g., a test DB) here.
    Base.metadata.create_all(engine)

    with app.test_client() as client:
        yield client

    # Optionally drop tables after tests, if you want a clean slate:
    # Base.metadata.drop_all(engine)

@pytest.fixture
def simple_jpeg():
    """
    Creates an in-memory JPEG image for uploading.
    """
    file = BytesIO()
    img = Image.new('RGB', (50, 50), color='blue')
    img.save(file, 'JPEG')
    file.seek(0)
    return file

def test_process_image_new_upload(test_client, simple_jpeg):
    """
    Test the /process-image route with a fresh image that
    hasn't been hashed or stored before.
    """
    data = {
        'image': (simple_jpeg, 'test_image.jpg')
    }
    response = test_client.post('/process-image', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    # We expect an image back, so let's check the Content-Type
    assert response.headers['Content-Type'] == 'image/jpeg'
    # We also expect an x-description header with JSON content
    assert 'x-description' in response.headers
    # The textual response is inside a JSON string in x-description
    # We can parse it if we want
    import json
    description = json.loads(response.headers['x-description'])
    assert "text" in description

def test_process_image_cached_upload(test_client, simple_jpeg):
    """
    Test that re-uploading the same image returns the cached response
    without reprocessing it.
    """
    def get_fresh_jpeg():
        """Helper function to create a fresh copy of simple_jpeg."""
        new_file = BytesIO(simple_jpeg.getvalue())  # Copy original bytes
        new_file.seek(0)
        return new_file

    # First upload
    response1 = test_client.post('/process-image', data={'image': (get_fresh_jpeg(), 'test_image.jpg')}, content_type='multipart/form-data')
    assert response1.status_code == 200

    # Second upload of the exact same image
    response2 = test_client.post('/process-image', data={'image': (get_fresh_jpeg(), 'test_image.jpg')}, content_type='multipart/form-data')
    assert response2.status_code == 200

    # Compare responses to ensure cached version is returned
    assert response1.headers['x-description'] == response2.headers['x-description']

def test_gallery_images(test_client):
    """
    Test the /api/gallery-images route.
    Depending on your local environment, you might have to mock the filesystem
    or place some test files in the uploads folder.
    """
    response = test_client.get('/api/gallery-images')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)  # should return a list of dicts
    # If your uploads folder is empty, this might be an empty list.
    # If you want to test with real or mock files,
    # create them before calling this test.
