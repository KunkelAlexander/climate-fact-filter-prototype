# tests/test_ai_service.py

import pytest
from unittest.mock import patch, MagicMock

import sys
import os

# setting path
sys.path.append(os.path.abspath('../'))

from ai_service import check_truth_with_chatgpt

@patch('ai_service.client.chat.completions.create')
def test_check_truth_with_chatgpt(mock_openai):
    """
    Mocks the OpenAI API call, ensuring we can test the function
    without making an actual network call.
    """
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Mocked answer"))]

    # Set the mock return value
    mock_openai.return_value = mock_response

    extracted_text = "Global warming is a hoax."
    response = check_truth_with_chatgpt(extracted_text)

    # The function should return "Mocked answer"
    assert response == "Mocked answer"
    mock_openai.assert_called_once()


# Import the objects from app.py
# (Adjust the import path if your "app.py" is in a different directory)
from app import (
    faiss_index,
    embedding_model,
    all_chunks,
    metadata,
    normalise,
    ALPHA,
    SELECTED_TYPES
)


@pytest.mark.asyncio
def test_check_truth_with_chatgpt():
    """
    Basic test to ensure that check_truth_with_chatgpt
    works without throwing exceptions and returns a non-empty response.
    """
    # 1. Create a sample statement
    test_text = "Electric vehicles emit more CO2 over their lifetime than diesel vehicles."

    # 2. Call the function
    response = check_truth_with_chatgpt(
        extracted_text=test_text,
        faiss_index=faiss_index,
        embedding_model=embedding_model,
        all_chunks=all_chunks,
        metadata=metadata,
        normalise=normalise,
        alpha=ALPHA,
        selected_types=SELECTED_TYPES,
        max_sources=5
    )

    # 3. Print the output (so you can see what it returns)
    print("\n[TEST OUTPUT] Response from check_truth_with_chatgpt:")
    print(response)
    print("------------------------------------------------------")

    # 4. Assert that we got back something non-empty
    assert response is not None, "The function returned None"
