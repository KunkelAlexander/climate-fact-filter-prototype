import React, { useState } from 'react';
import './App.css';

function App() {
  const [image, setImage] = useState(null);
  const [progress, setProgress] = useState(0);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisText, setAnalysisText] = useState('');

  // Handle image upload
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setImage(URL.createObjectURL(file));
      setProgress(0);
      setAnalysisText(''); // Clear analysis text on new upload
    }
  };

  // Simulate analysis process
  const analyzeImage = () => {
    setAnalyzing(true);
    setProgress(0);
    setAnalysisText(''); // Clear text before new analysis

    const interval = setInterval(() => {
      setProgress((prevProgress) => {
        if (prevProgress >= 100) {
          clearInterval(interval);
          setAnalyzing(false);
          setAnalysisText('Analysis complete! This is where the analysis results would appear.');
          return 100;
        }
        return prevProgress + 10;
      });
    }, 500);
  };

  // Download function (not implemented, placeholder for now)
  const downloadImage = () => {
    alert('Download functionality would go here.');
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
          <button onClick={downloadImage} className="download-button" disabled={!image || analyzing}>
            Download
          </button>
          {analyzing && (
            <div className="progress-container">
              <div className="progress-bar" style={{ width: `${progress}%` }}></div>
              <span>{progress}%</span>
            </div>
          )}
          {analysisText && <p className="analysis-text">{analysisText}</p>}
        </div>

        {/* Right Column - Image Preview */}
        <div className="right-column">
          {image && (
            <div className="image-preview">
              <img src={image} alt="Uploaded Preview" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
