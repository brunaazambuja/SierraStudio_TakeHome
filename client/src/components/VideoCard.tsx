import DeleteIcon from '@mui/icons-material/Delete';
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Stack,
  Typography,
} from '@mui/material';
import { Link } from 'react-router-dom';
import type { Video } from '../services/videoService';

interface VideoCardProps {
  video: Video;
  onDelete: (videoName: string) => void;
  loadingDelete: string | null;
}

export default function VideoCard({
  video,
  onDelete,
  loadingDelete,
}: VideoCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    if (confirm(`Are you sure you want to delete "${video.display_name}"?`)) {
      onDelete(video.base_name);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US');
  };

  const formatSize = (bytes: number) => {
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  return (
    <Card
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        p: 2,
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 4,
        },
      }}
    >
      {video.poster_url && (
        <img src={video.poster_url} height={100} alt="Poster" />
      )}
      <CardContent sx={{ flex: 1, py: 0 }}>
        <Typography
          variant="h6"
          component={Link}
          to={`/watch/${video.base_name}`}
          sx={{
            textDecoration: 'none',
            color: 'primary.main',
            '&:hover': { textDecoration: 'underline' },
          }}
        >
          {video.display_name}
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {formatSize(video.size)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {formatDate(video.last_modified)}
          </Typography>
          {video.resolutions && video.resolutions.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Available:
              </Typography>
              {video.resolutions.map((resolution) => (
                <Chip
                  key={resolution}
                  label={resolution}
                  size="small"
                  sx={{ fontSize: '0.75rem', height: '20px' }}
                />
              ))}
            </Box>
          )}
        </Stack>
      </CardContent>
      {loadingDelete === video.base_name ? (
        <CircularProgress />
      ) : (
        <IconButton
          color="error"
          onClick={handleDelete}
          aria-label="delete"
          sx={{ ml: 2 }}
        >
          <DeleteIcon />
        </IconButton>
      )}
    </Card>
  );
}
