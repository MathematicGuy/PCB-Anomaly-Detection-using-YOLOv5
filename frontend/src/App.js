import React, { useState } from 'react';
import axios from 'axios';
import './app.css';

const BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [uploadedImages, setUploadedImages] = useState([]);
  const [processedImages, setProcessedImages] = useState([]);

  const handleUpload = async (e) => {
    const files = e.target.files;
    const formData = new FormData();
    formData.append('file', files[0]);

    const response = await axios.post(`${BASE_URL}/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    setUploadedImages([...uploadedImages, files[0].name]);
  };

  const handleProcess = async () => {
    await axios.post(`${BASE_URL}/process/`);
    setProcessedImages(uploadedImages);
  };

  return (
    <div className="App">
      <Header />
      <div className="container">
        <div className="upload-section">
          <input type="file" onChange={handleUpload} />
          <div className="uploaded-images">
            <h3>Uploaded Images</h3>
            <ul>
              {uploadedImages.map((img, idx) => (
                <li key={idx}>{img}</li>
              ))}
            </ul>
          </div>
        </div>
        <div className="processed-section">
          <h3>Processed Images</h3>
          <ul>
            {processedImages.map((img, idx) => (
              <li key={idx}>
                <a href={`${BASE_URL}/processed/${img}`} download>{img}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <button onClick={handleProcess}>Process Images</button>
      <Footer />
    </div>
  );
}

function Header() {
  return <header><h1>Image Processing App</h1></header>;
}

function Footer() {
  return <footer><p>© 2024 Image Processor</p></footer>;
}

export default App;
