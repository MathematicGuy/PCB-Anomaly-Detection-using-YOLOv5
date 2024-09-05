import React, { useState } from 'react';
import axios from 'axios';
import { Button, CircularProgress, Container, Grid, Card, Typography } from '@mui/material';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './app.css'; // Your custom styles

const BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [uploadedImages, setUploadedImages] = useState([]);
  const [processedImages, setProcessedImages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e) => {
    setLoading(true);
    const files = e.target.files;
    const formData = new FormData();
    formData.append('file', files[0]);

    try {
      await axios.post(`${BASE_URL}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success('File uploaded successfully!');
      setUploadedImages([...uploadedImages, files[0].name]);
    } catch (err) {
      toast.error('Failed to upload file.');
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    setLoading(true);
    try {
      await axios.post(`${BASE_URL}/process/`);
      toast.success('Images processed successfully!');
      setProcessedImages(uploadedImages); // Display processed images
    } catch (err) {
      toast.error('Failed to process images.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <ToastContainer />
      <Header />

      <Grid container spacing={4} className="main-container">
        <Grid item xs={12} md={6}>
          <Card className="upload-section">
            <Typography variant="h5" gutterBottom>
              Upload Images
            </Typography>
            <input type="file" onChange={handleUpload} />
            <ul>
              {uploadedImages.map((img, idx) => (
                <li key={idx}>{img}</li>
              ))}
            </ul>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card className="processed-section">
            <Typography variant="h5" gutterBottom>
              Processed Images
            </Typography>
            <ul>
              {processedImages.map((img, idx) => (
                <li key={idx}>
                  <a href={`${BASE_URL}/processed/${img}`} download>
                    {img}
                  </a>
                </li>
              ))}
            </ul>
          </Card>
        </Grid>
      </Grid>

      <div className="process-button">
        <Button variant="contained" color="primary" onClick={handleProcess} disabled={loading || uploadedImages.length === 0}>
          {loading ? <CircularProgress size={24} /> : 'Process Images'}
        </Button>
      </div>

      <Footer />
    </Container>
  );
}

function Header() {
  return (
    <header className="header">
      <Typography variant="h4" gutterBottom>
        Image Processing App
      </Typography>
    </header>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <Typography variant="body2">
        © 2024 Image Processor. All rights reserved.
      </Typography>
    </footer>
  );
}

export default App;
