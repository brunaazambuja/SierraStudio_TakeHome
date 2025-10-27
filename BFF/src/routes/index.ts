import { Router } from 'express';
import multer from 'multer';
import * as videoController from '../controllers/videoController';
import { uploadVideoHandler } from '../controllers/videoController';

const routes = Router();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 1000 * 1024 * 1024,
  },
});

routes.get('/videos', videoController.listVideos);
routes.get('/videos/:videoName', videoController.streamVideo);
routes.delete('/videos/:videoName', videoController.deleteVideoHandler);
routes.post('/upload', upload.single('video_file'), uploadVideoHandler);

export default routes;
