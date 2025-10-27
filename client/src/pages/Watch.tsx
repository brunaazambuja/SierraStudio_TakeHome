import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Typography,
} from '@mui/material';
import { useEffect, useRef, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import type { Video } from '../services/videoService';
import { videoService } from '../services/videoService';

export default function Watch() {
  const { videoName } = useParams<{ videoName: string }>();
  const [video, setVideo] = useState<Video | null>(null);
  const [selectedQuality, setSelectedQuality] = useState('720p');
  const [loading, setLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const fetchVideoInfo = async () => {
      if (!videoName) return;

      try {
        setLoading(true);
        const videos = await videoService.getAllVideos();
        const videoData = videos.find((v) => v.base_name === videoName);

        if (videoData) {
          setVideo(videoData);
          setSelectedQuality(selectedQuality);
        }
      } catch (err) {
        console.error('Error fetching video info:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchVideoInfo();
  }, [videoName, selectedQuality]);

  const handleQualityChange = (newQuality: string) => {
    if (!videoRef.current) return;
    setSelectedQuality(newQuality);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!video || !videoName) {
    return (
      <Box>
        <Typography variant="h5" color="error">
          Video not found
        </Typography>
        <Button
          component={RouterLink}
          to="/"
          startIcon={<ArrowBackIcon />}
          sx={{ mt: 2 }}
        >
          Back to Home
        </Button>
      </Box>
    );
  }

  return (
    <>
      <Typography variant="h4" component="h2" gutterBottom>
        {video.display_name}
      </Typography>

      {video.resolutions && video.resolutions.length > 0 && (
        <Paper
          sx={{ p: 2, mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}
        >
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Quality</InputLabel>
            <Select
              value={selectedQuality}
              label="Quality"
              onChange={(e) => handleQualityChange(e.target.value)}
            >
              {video.resolutions.map((resolution) => (
                <MenuItem key={resolution} value={resolution}>
                  {resolution}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {video.thumbnail_strip_url && (
            <img
              src={video.thumbnail_strip_url}
              height={100}
              alt="Thumbnail Strip"
            />
          )}
        </Paper>
      )}

      <Box
        component="video"
        ref={videoRef}
        controls
        autoPlay
        sx={{
          width: '100%',
          maxWidth: '100%',
          borderRadius: 1,
          boxShadow: 3,
        }}
      >
        <source
          src={videoService.getVideoUrl(videoName, selectedQuality)}
          type="video/mp4"
        />
      </Box>

      <Button
        component={RouterLink}
        to="/"
        startIcon={<ArrowBackIcon />}
        variant="outlined"
        sx={{ mt: 3 }}
      >
        Back to Home
      </Button>
    </>
  );
}
