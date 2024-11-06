import React, { useState } from 'react';
import './App.css';

function App() {
  const [image, setImage] = useState(null);
  const [progress, setProgress] = useState(0);
  const [analyzing, setAnalyzing] = useState(false);

  // Handle image upload
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setImage(URL.createObjectURL(file));
      setProgress(0); // Reset progress for new image
    }
  };

  // Simulate analysis process
  const analyzeImage = () => {
    setAnalyzing(true);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((prevProgress) => {
        if (prevProgress >= 100) {
          clearInterval(interval);
          setAnalyzing(false); // End analysis
          return 100;
        }
        return prevProgress + 10; // Increase progress by 10% every second
      });
    }, 500); // Adjust speed here
  };

  return (
    <div className="App">
      <h1>Climate Truth Filter</h1>
      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="upload-button"
      />
      {image && (
        <>
          <div className="image-preview">
            <img src={image} alt="Uploaded Preview" />
          </div>
          <button onClick={analyzeImage} className="analyze-button" disabled={analyzing}>
            {analyzing ? 'Analyzing...' : 'Analyze Image'}
          </button>
          {analyzing && (
            <div className="progress-container">
              <div className="progress-bar" style={{ width: `${progress}%` }}></div>
              <span>{progress}%</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;
