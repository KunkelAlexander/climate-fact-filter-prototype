import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const uploadImageToCloudinary = async (imagePath) => {

};

function App() {
  const [image, setImage] = useState(null);
  const [activeTab, setActiveTab] = useState('sharepic'); // State to manage active tab
  const [processedImage, setProcessedImage] = useState(null);
  const [analysisText, setAnalysisText] = useState(''); // New state for analysis text
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedImageUrl, setUploadedImageUrl] = useState(null);
  const [galleryImages, setGalleryImages] = useState([]);

  // Replace 127.0.0.1:5000 with the actual IP and port of your backend server
  const BACKEND_URL = 'http://127.0.0.1:5000';

  useEffect(() => {
    if (activeTab === 'gallery') {
      fetch(`${BACKEND_URL}/api/gallery-images`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log("Fetched gallery images:", data);
          setGalleryImages(data);
        })
        .catch(error => console.error('Error fetching gallery images:', error));
    }
  }, [activeTab]);


  function showTab(tabName) {
    const tabs = document.querySelectorAll('.content');
    const buttons = document.querySelectorAll('.tab-selector button');

    // Hide all content divs and remove active class from all buttons
    tabs.forEach(tab => tab.style.display = 'none');
    buttons.forEach(button => button.classList.remove('active'));

    // Show the selected tab content and activate the corresponding button
    document.getElementById(tabName).style.display = 'block';
    document.querySelector(`.tab-selector button[onclick="showTab('${tabName}')"]`).classList.add('active');
  }


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
          <div className="header">
          <img src="/logo.jpg" alt="Fuel Fake Filter Logo" className="logo" />
          <h1>Fuel Fake Filter</h1>
        </div>

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

          {/* Social media share icons */}
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

        {/* Right Column */}
        <div className="right-column">
          {/* Tab Selector */}
          <div className="tab-container">
          <div className="tab-selector">
            <button
              className={activeTab === 'sharepic' ? 'active' : ''}
              onClick={() => setActiveTab('sharepic')}
            >
              True or Fake?
            </button>
            <button
              className={activeTab === 'gallery' ? 'active' : ''}
              onClick={() => setActiveTab('gallery')}
            >
              Gallery
            </button>
            <button
              className={activeTab === 'dashboard' ? 'active' : ''}
              onClick={() => setActiveTab('dashboard')}
            >
              Dashboard
            </button>
          </div></div>

          {/* Tab Content */}
          {activeTab === 'sharepic' && (
            <>
              <div className="image-grid">
                {image && (
                  <div className="image-preview">
                    <h3>True?</h3>
                    <img src={URL.createObjectURL(image)} alt="True sharepic?" />
                  </div>
                )}
                {processedImage && (
                  <div className="image-preview">
                    <h3>Fake!</h3>
                    <img src={processedImage} alt="Fake!" />
                  </div>
                )}
              </div>

              {/* Analysis Box below the image-grid */}
              {analysisText && (
                <div className="analysis-box">
                  <p>{analysisText}</p>
                </div>
              )}
            </>
          )}

          {activeTab === 'gallery' && (
            <div className="gallery-grid">
              {galleryImages.length > 0 ? (
                galleryImages.map((imagePair, index) => (
                  <div key={index} className="gallery-item">
                    <div className="image-preview">
                      <h3>True?</h3>
                      <img src={`C:/Users/TE/Documents/fake_news_sharepics/uploads/${imagePair.input}`} alt="True sharepic?" />
                    </div>
                    <div className="image-preview">
                      <h3>Fake!</h3>
                      <img src={`C:/Users/TE/Documents/fake_news_sharepics/uploads/${imagePair.output}`} alt="Fake sharepic" />
                    </div>
                  </div>
                ))
              ) : (
                <p>No images available in the gallery.</p>
              )}
            </div>
          )}


          {activeTab === 'dashboard' && (
            <div className="dashboard-content">
              <iframe
                title="Fuel Fake Filter"
                width="100%"
                height="300%"
                src="https://app.powerbi.com/view?r=eyJrIjoiYzc5MWNlZDYtZDNhYy00YjZiLTk4M2QtYzk3NzYxM2NhYjJmIiwidCI6ImEwODJkYmJjLWQ4OWQtNDAxOC1iMzM2LTcyNzlmMjIxNzdlYiIsImMiOjl9"
                frameBorder="0"
                allowFullScreen="true"
              ></iframe>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;