import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [image, setImage] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Handle image upload
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setImage(file);
      setProcessedImage(null); // Clear any previous result
    }
  };

  // Send the image to the Python backend for processing
  const analyzeImage = async () => {
    if (!image) return;

    setAnalyzing(true);
    const formData = new FormData();
    formData.append('image', image);

    try {
      const response = await axios.post('http://127.0.0.1:5000/process-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob', // Receive the image as a blob
      });

      // Convert the response blob to a URL and set it for display
      const url = URL.createObjectURL(response.data);
      setProcessedImage(url);
    } catch (error) {
      console.error("Error processing the image:", error);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        {/* Left Column - User Interface */}
        <div className="left-column">
          <h1>Image Analysis</h1>
          <input type="file" accept="image/*" onChange={handleImageUpload} className="upload-button" />
          <button onClick={analyzeImage} className="analyze-button" disabled={!image || analyzing}>
            {analyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {/* Right Column - Display Original and Processed Images */}
        <div className="right-column">
          {image && (
            <div className="image-preview">
              <h2>Original Image</h2>
              <img src={URL.createObjectURL(image)} alt="Uploaded" />
            </div>
          )}
          {processedImage && (
            <div className="image-preview">
              <h2>Processed Image</h2>
              <img src={processedImage} alt="Processed" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
