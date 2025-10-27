import { Alert, Box, CircularProgress, Stack, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import VideoCard from '../components/VideoCard';
import { useToast } from '../context/ToastContext';
import type { Video } from '../services/videoService';
import { videoService } from '../services/videoService';

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingDelete, setLoadingDelete] = useState<string | null>(null);
  const { showToast } = useToast();

  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await videoService.getAllVideos();
      console.log(data);
      setVideos(data);
    } catch (err) {
      setError('Failed to load videos');
      console.error('Error fetching videos:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleDelete = async (videoName: string) => {
    try {
      setLoadingDelete(videoName);
      await videoService.deleteVideo(videoName);
      setLoadingDelete(null);

      showToast('Video deleted successfully!', 'success');
      setVideos((prev) => prev.filter((v) => v.base_name !== videoName));
    } catch (err) {
      showToast('Failed to delete video', 'error');
      console.error('Error deleting video:', err);
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '50vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <>
      <Typography variant="h4" component="h2" gutterBottom>
        Available Videos
      </Typography>

      {videos.length === 0 ? (
        <Link to="/upload" style={{ color: '#1976d2' }}>
          Upload Video
        </Link>
      ) : (
        <Stack spacing={2}>
          {videos.map((video) => (
            <VideoCard
              key={video.base_name}
              video={video}
              onDelete={handleDelete}
              loadingDelete={loadingDelete}
            />
          ))}
        </Stack>
      )}
    </>
  );
}
