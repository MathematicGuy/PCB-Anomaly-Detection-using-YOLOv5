import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button, CircularProgress, Container, Grid, Card, Typography } from '@mui/material';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './app.css'; // Your custom styles

const BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [uploadedImages, setUploadedImages] = useState([]);
  const [latestProsFolder, setLatestProsFolder] = useState('');
  const [latestProsFiles, setLatestProsFiles] = useState([]);
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
      fetchLatestProsFolder(); // Fetch the latest processed folder after processing
    } catch (err) {
      toast.error('Failed to process images.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadAll = async () => {
    try {
      const response = await axios({
        url: `${BASE_URL}/download-latest-pros/`,
        method: 'GET',
        responseType: 'blob', // Important to download files
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `latest_pros.zip`); // Set download name
      document.body.appendChild(link);
      link.click(); // Trigger download
      link.remove(); // Clean up

      toast.success('Downloaded all images successfully!');
    } catch (err) {
      toast.error('Failed to download images.');
    }
  };

  const fetchLatestProsFolder = async () => {
    try {
      const response = await axios.get(`${BASE_URL}/latest-pros/`);
      setLatestProsFolder(response.data.folder);
      setLatestProsFiles(response.data.files);
    } catch (err) {
      toast.error('Failed to fetch the latest processed folder.');
    }
  };

  useEffect(() => {
    // Fetch the latest pros folder on component mount
    fetchLatestProsFolder();
  }, []);

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
              Latest Processed Images ({latestProsFolder})
            </Typography>
            <ul>
              {latestProsFiles.map((img, idx) => (
                <li key={idx}>
                  <a href={`${BASE_URL}/processed/${latestProsFolder}/${img}`} download>
                    {img}
                  </a>
                </li>
              ))}
            </ul>
            <Button variant="contained" color="secondary" onClick={handleDownloadAll}>
              Download All
            </Button>
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
