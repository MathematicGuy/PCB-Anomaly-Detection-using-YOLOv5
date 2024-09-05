import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button, CircularProgress, Container, Grid, Card, Typography, Box, IconButton } from '@mui/material';
import { Delete } from '@mui/icons-material';
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
    const files = e.target.files;
    const formData = new FormData();
    formData.append('file', files[0]);

    setLoading(true);

    try {
      await axios.post(`${BASE_URL}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('File uploaded successfully!');
      setUploadedImages([...uploadedImages, files[0].name]);
    } catch (err) {
      toast.error('Failed to upload file.');
    } finally {
      setLoading(false);
    }
  };

    const handleDeleteImage = async (fileName) => {
      setLoading(true);
      try {
        await axios.delete(`${BASE_URL}/delete/${fileName}`);
        toast.success(`'${fileName}' deleted successfully!`);
        const updatedImages = uploadedImages.filter((img) => img !== fileName);
        setUploadedImages(updatedImages);
      } catch (err) {
        toast.error(`Failed to delete '${fileName}'`);
      } finally {
        setLoading(false);
      }
    };

  const handleProcess = async () => {
    setLoading(true);
    try {
      await axios.post(`${BASE_URL}/process/`);
      toast.success('Images processed successfully!');
      fetchLatestProsFolder();
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
          responseType: 'blob',
        });

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');

        // Set the download name as the latest folder name (latestProsFolder)
        link.href = url;
        link.setAttribute('download', `${latestProsFolder}.zip`); // Use the folder name instead of 'latest_pros.zip'

        document.body.appendChild(link);
        link.click();
        link.remove();

        toast.success(`Downloaded all images from ${latestProsFolder} successfully!`);
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
    fetchLatestProsFolder();
  }, []);

  return (
    <Container
      maxWidth="md"
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        backgroundColor: '#f9f9f9',
        padding: '2rem',
      }}
    >
      <ToastContainer />
      <Header />

      {/* Main content area */}
      <Box sx={{ flexGrow: 1 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card
              sx={{
                padding: '2rem',
                borderRadius: '12px',
                boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.1)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Typography variant="h5" gutterBottom sx={{ color: '#333' }}>
                Upload Images
              </Typography>
              <input type="file" onChange={handleUpload} />
              <Box component="ul" sx={{ listStyle: 'none', paddingLeft: 0, marginTop: '1rem' }}>
                {uploadedImages.map((img, idx) => (
                  <li
                    key={idx}
                    style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem', color: '#666' }}
                  >
                    <Typography variant="body1" sx={{ flexGrow: 1 }}>
                      {img}
                    </Typography>
                    <IconButton
                      aria-label="delete"
                      onClick={() => handleDeleteImage(img)}
                      sx={{ color: '#f44336' }}
                    >
                      <Delete />
                    </IconButton>
                  </li>
                ))}
              </Box>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card
              sx={{
                padding: '2rem',
                borderRadius: '12px',
                boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.1)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Typography variant="h5" gutterBottom sx={{ color: '#333' }}>
                Processed Images ({latestProsFolder})
              </Typography>
              <Box component="ul" sx={{ listStyle: 'none', paddingLeft: 0, marginTop: '1rem' }}>
                {latestProsFiles.map((img, idx) => (
                  <li key={idx}>
                    <a href={`${BASE_URL}/processed/${latestProsFolder}/${img}`} download style={{ color: '#1976d2' }}>
                      {img}
                    </a>
                  </li>
                ))}
              </Box>
              <Button
                variant="contained"
                color="secondary"
                sx={{ marginTop: '1rem', backgroundColor: '#1976d2' }}
                onClick={handleDownloadAll}
              >
                Download All
              </Button>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Process button moved outside the grid to ensure visibility */}
      <Box sx={{ marginTop: '2rem', textAlign: 'center' }}>
        <Button variant="contained" color="primary" onClick={handleProcess} disabled={loading || uploadedImages.length === 0}>
          {loading ? <CircularProgress size={24} /> : 'Process Images'}
        </Button>
      </Box>

      {/* Footer at the bottom */}
      <Footer />
    </Container>
  );
}

function Header() {
  return (
    <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: '#333' }}>
        Image Processing App
      </Typography>
    </header>
  );
}

function Footer() {
  return (
    <footer style={{ textAlign: 'center', padding: '1rem 0' }}>
      <Typography variant="body2" sx={{ color: '#aaa' }}>
        © 2024 Image Processor. All rights reserved.
      </Typography>
    </footer>
  );
}

export default App;
