import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const uploadImageToCloudinary = async (imagePath) => {

};

function App() {
  const [image, setImage] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [analysisText, setAnalysisText] = useState(''); // New state for analysis text
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedImageUrl, setUploadedImageUrl] = useState(null);



  // Handle share action based on the selected platform
  const handleShare = async (platform) => {
    // Check if image URL is already uploaded; if not, upload the image
    if (!uploadedImageUrl && processedImage) {

      const uploadedUrl = await uploadImageToCloudinary(processedImage);
      setUploadedImageUrl(uploadedUrl);
    }

    // Define the share URLs for each platform
    const shareLinks = {
      twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(uploadedImageUrl)}&text=Check out this verified image!`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(uploadedImageUrl)}`,
      instagram: uploadedImageUrl // Instagram download link (since direct sharing isn't supported)
    };

    // Open the share link in a new tab based on the platform
    if (platform === "instagram") {
      // Instagram: Use a download link
      const link = document.createElement('a');
      link.href = uploadedImageUrl;
      link.download = 'verified_image.jpg';
      link.click();
    } else {
      // For Twitter and Facebook, open the share URL in a new window
      window.open(shareLinks[platform], '_blank', 'noopener,noreferrer');
    }
  };

  // Handle image upload
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setImage(file);
      setProcessedImage(null); // Clear any previous result
      setAnalysisText('');     // Clear previous analysis text
      setProgress(0);          // Reset progress
    }
  };


  const triggerFileInput = () => {
    document.getElementById('hidden-file-input').click();
  };

  // Simulate progress bar during analysis
  const simulateProgress = () => {
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prevProgress) => {
        if (prevProgress >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prevProgress + 10;
      });
    }, 200); // 2-second total delay (200 ms increments)
  };

  // Send the image to the Python backend for processing
  const analyzeImage = async () => {
    if (!image) return;

    setAnalyzing(true);
    simulateProgress();

    const formData = new FormData();
    formData.append('image', image);

    try {
      // Send the image to the backend
      const response = await axios.post('http://127.0.0.1:5000/process-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob', // Receive the image as a blob
      });

      // Revoke any previous URL to avoid memory leaks
      if (processedImage) {
        URL.revokeObjectURL(processedImage);
      }

      // Convert the response blob to a URL and set it for display
      const processedImageUrl = URL.createObjectURL(response.data);
      setProcessedImage(processedImageUrl);

      // Retrieve the analysis text from the response header
      const analysisTextHeader = response.headers['x-description'];
      if (analysisTextHeader) {
        const analysisTextJSON = JSON.parse(analysisTextHeader);
        setAnalysisText(analysisTextJSON.text); // Set the analysis text
        console.log(analysisTextJSON.text);
      }
    } catch (error) {
      console.error("Error processing the image:", error);
    } finally {
      setAnalyzing(false);
      setProgress(100); // Ensure progress reaches 100%
    }
  };

  // Download the processed image
  const downloadImage = () => {
    if (processedImage) {
      const link = document.createElement('a');
      link.href = processedImage;
      link.download = 'processed_image.jpg';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="App">
      <div className="container">
        {/* Left Column - User Interface */}
        <div className="left-column">
          <h1>Climate Fact Filter</h1>


          {/* Hidden file input */}
          <input
            type="file"
            id="hidden-file-input"
            accept="image/*"
            onChange={handleImageUpload}
            className="upload-button-hidden"  // Class to hide the input
          />
          {/* Custom upload button */}
          <button onClick={triggerFileInput} className="upload-button">
            Upload
          </button>
          <button onClick={analyzeImage} className="analyze-button" disabled={!image || analyzing}>
            {analyzing ? 'Analyzing...' : 'Analyze'}
          </button>
          {analyzing && (
            <div className="progress-container">
              <div className="progress-bar" style={{ width: `${progress}%` }}></div>
              <span>{progress}%</span>
            </div>
          )}
          <button onClick={downloadImage} className="download-button" disabled={!processedImage}>
            Download
          </button>
          {analysisText && <p className="analysis-text">{analysisText}</p>}

          {/* Share Buttons */}
          {/* Social media share icons */}
          <div className="share-buttons">
            <div className="social-icons">
              <a onClick={() => handleShare("twitter")} style={{ cursor: 'pointer' }}>
                <i className="fab fa-twitter"></i> Twitter
              </a>

              <a onClick={() => handleShare("facebook")} style={{ cursor: 'pointer' }}>
                <i className="fab fa-facebook"></i> Facebook
              </a>

              <a onClick={() => handleShare("instagram")} style={{ cursor: 'pointer' }}>
                <i className="fab fa-instagram"></i> Instagram
              </a>
            </div>
          </div>
        </div>

        {/* Right Column - Display Original and Processed Images */}
        <div className="right-column">
          {image && (
            <div className="image-preview">
              <h2>True?</h2>
              <img src={URL.createObjectURL(image)} alt="True sharepic?" />
            </div>
          )}
          {processedImage && (
            <div className="image-preview">
              <h2>Fake!</h2>
              <img src={processedImage} alt="Fake!" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;