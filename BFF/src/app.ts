import cors from 'cors';
import dotenv from 'dotenv';
import express, { Request, Response } from 'express';
import routes from './routes';

dotenv.config();
export const app = express();

const DEFAULT_CORS_HOSTS = 'http://localhost:5173';

app.use(
  cors({
    origin: DEFAULT_CORS_HOSTS,
    credentials: false,
  })
);

app.use((_, res, next) => {
  res.setHeader('Cache-Control', 'no-store');
  res.removeHeader('Last-Modified');
  next();
});

app.use(express.json({ limit: '10mb' }));
app.use('/api', routes);

app.get('/', (req: Request, res: Response) => {
  res.send('Express + TypeScript Server');
});

app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});
