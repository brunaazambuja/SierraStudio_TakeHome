# Setup Instructions

1. **Processor** (FastAPI) - Handles video processing and storage
2. **BFF** (Express/TypeScript) - Backend for Frontend, proxies requests
3. **Client** (React) - User interface

## Architecture Flow

```
Client (Port 5173) → BFF (Port 3000) → Processor/FastAPI (Port 8000) → Cloudflare R2
```

## Setup Steps

### 1. Processor (FastAPI)

```bash
./run.sh
```

The FastAPI server will be available at `http://localhost:8000`

### 2. BFF (Backend For Frontend)

```bash
npm install
npm run dev
```

The BFF server will be available at `http://localhost:3000`

### 3. Client (React)

```bash
npm install
npm run dev
```

The client will be available at `http://localhost:5173`

## Testing the Connection

1. Start all three servers in order:
   - Processor (FastAPI) on port 8000
   - BFF (Express) on port 3000
   - Client (React) on port 5173

2. Open your browser and navigate to `http://localhost:5173`

3. You should see the Video App interface with:
   - Home page showing available videos
   - Upload page for uploading new videos
   - Watch page for viewing videos with quality selection

## API Endpoints

### BFF Endpoints (Port 3000)
- `GET /api/videos` - List all videos
- `GET /api/videos/:videoName?resolution=720p` - Stream a video
- `POST /api/upload` - Upload a new video
- `DELETE /api/videos/:videoName` - Delete a video

### FastAPI Endpoints (Port 8000)
- `GET /videos` - List all videos (JSON)
- `GET /videos/{video_name}?resolution=720p` - Stream video
- `POST /upload` - Upload video
- `DELETE /videos/{video_name}` - Delete video
- `GET /` - Web interface (HTML)
- `GET /upload` - Upload form (HTML)
- `GET /watch/{video_name}` - Watch video (HTML)


### CORS
The BFF is configured to accept requests from `http://localhost:5173` which is the frontend url

### Processor (.env)
```
R2_ACCOUNT_ID=f9168b31c6084558d6900e32e3fcc67b
R2_ACCESS_KEY_ID=74d0d2fa0ad2da809c71c0d6d70dfc8a
R2_SECRET_ACCESS_KEY=f5f4d5461b8980b46bf1a01cfa07c06d323379e65c8b1270cd24cf3429dd08b9
R2_BUCKET_NAME=sierra-video-stream
MAX_VIDEO_SIZE_MB=1000
```

### BFF (.env)
```
CORS_HOSTS=localhost,http://localhost:3000,http://localhost:3003
FASTAPI_URL='http://localhost:8000'
PORT=3000
```

### Client (.env)
```
VITE_API_URL=http://localhost:3000/api
```


## Demos

Some demos can be found on the demo folder