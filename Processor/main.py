import os
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, StreamingResponse, JSONResponse
from dotenv import load_dotenv
import httpx
from processing import VideoValidator, VideoTranscoder, ThumbnailGenerator
from storage import CloudflareR2Storage

load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="templates")

R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
MAX_VIDEO_SIZE_MB = int(os.getenv('MAX_VIDEO_SIZE_MB')) 

r2_storage = CloudflareR2Storage(
    account_id=R2_ACCOUNT_ID,
    access_key_id=R2_ACCESS_KEY_ID,
    secret_access_key=R2_SECRET_ACCESS_KEY,
    bucket_name=R2_BUCKET_NAME
)

@app.get('/videos')
async def list_videos():
    videos = r2_storage.list_videos_grouped()
    return JSONResponse(content=videos)


@app.get('/videos/{video_name}')
async def get_video(video_name: str, resolution: str = Query(default='720p')):
    video_url = r2_storage.get_video_url_by_resolution(video_name, resolution)
    
    if not video_url:
        return {'error': 'video not found'}
    
    async def video_stream():
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', video_url, headers={'Range': 'bytes=0-'}, timeout=None) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk 
    return StreamingResponse(video_stream(), media_type='video/mp4')


@app.get('/watch/{video_name}', response_class=JSONResponse)
async def watch_video(_: Request, video_name: str):
    base_name = video_name.rsplit('.', 1)[0]
    for res in ['_360p', '_720p', '_1080p', '_original']:
        if base_name.endswith(res):
            base_name = base_name[:-len(res)]
            break
    
    title = base_name.replace('_', ' ')
    
    # Get available resolutions for this video
    available_resolutions = r2_storage.get_available_resolutions(video_name)
    
    return {
        'video_name': base_name,
        'title': title,
        'available_resolutions': available_resolutions
    }


@app.post('/upload')
async def upload_video(_: Request, title: str = Form(...), video_file: UploadFile = File(...)):
    try:
        video_content = await video_file.read()
        
        # check for corruption
        is_valid, message, details = VideoValidator.validate_video(
            video_file.filename,
            video_file.content_type,
            video_content,
            max_size_mb=MAX_VIDEO_SIZE_MB
        )
        
        if not is_valid:
            return {
                'message': f'Video validation failed: {message}',
                'error_details': details,
                'error': True
            }
        
        title_parsed = title.strip().replace(' ', '_')
        base_filename = title_parsed
        
        # Check if any resolution of this video already exists
        existing_resolutions = r2_storage.get_available_resolutions(base_filename)
        if existing_resolutions:
            return {
                'message': f'"{title}" already exists. Choose a different name.',
                'error': True
            }

        # Generate poster and thumbnail strip
        print(f"Generating poster image and thumbnail strip for video: {title}")
        thumbnails = {
            'poster': ThumbnailGenerator.generate_poster(video_content),
            'thumbnail_strip': ThumbnailGenerator.generate_thumbnail_strip(video_content)
        }
        
        # Upload thumbnails to R2
        poster_uploaded = False
        thumbnail_strip_uploaded = False
        
        if thumbnails['poster']:
            poster_uploaded = r2_storage.upload_image(
                thumbnails['poster'],
                f"{base_filename}_poster.jpg",
                'image/jpeg'
            )
            if poster_uploaded:
                print("Poster image uploaded successfully")
            else:
                print("Failed to upload poster image")
        
        if thumbnails['thumbnail_strip']:
            thumbnail_strip_uploaded = r2_storage.upload_image(
                thumbnails['thumbnail_strip'],
                f"{base_filename}_thumbnail_strip.png",
                'image/png'
            )
            if thumbnail_strip_uploaded:
                print("Thumbnail strip uploaded successfully")
            else:
                print("Failed to upload thumbnail strip")
        
        # Transcode video to multiple resolutions
        print(f"Starting transcoding for video: {title}")
        print(f"Original resolution: {details.get('resolution', 'unknown')}")
        
        try:
            transcoded_videos = VideoTranscoder.transcode_to_multiple_resolutions(
                input_content=video_content,
            )
            
            if not transcoded_videos:
                # If transcoding failed, upload original
                print("Transcoding failed, uploading original video")
                success = r2_storage.upload_video(
                    file_content=video_content,
                    filename=f"{base_filename}_original.mp4",
                    content_type=video_file.content_type
                )
                
                if not success:
                    return {
                        'message': 'Failed to upload video to storage. Please try again.',
                        'error': True
                    }
                
                resolutions_text = "transcoding failed - saved only original video"
            else:
                # Upload all transcoded versions
                upload_results = r2_storage.upload_video_resolutions(
                    video_data=transcoded_videos,
                    base_filename=base_filename,
                    content_type='video/mp4'
                )
                
                successful_uploads = [res for res, success in upload_results.items() if success]
                failed_uploads = [res for res, success in upload_results.items() if not success]
                
                if not successful_uploads:
                    return {
                        'message': 'Failed to upload video to storage. Please try again.',
                        'error': True
                    }
                
                if failed_uploads:
                    print(f"Some resolutions failed to upload: {failed_uploads}")
                
                resolutions_text = ', '.join(successful_uploads)
                print(f"Successfully uploaded resolutions: {resolutions_text}")
                
        except Exception as transcode_error:
            print(f"Transcoding error: {transcode_error}")
            # Fallback to uploading original
            success = r2_storage.upload_video(
                file_content=video_content,
                filename=f"{base_filename}_original.mp4",
                content_type=video_file.content_type
            )
            
            if not success:
                return {
                    'message': 'Failed to upload video to storage. Please try again.',
                    'error': True
                }
            
            resolutions_text = "transcoding error - saved only original video"
        
        video_info = f"Resolution: {details.get('resolution', 'N/A')}, Duration: {details.get('duration_seconds', 'N/A')}s"
        
        return {
            'message': f'Video "{title}" uploaded successfully! Available in: {resolutions_text}. ({video_info})',
            'video_details': details
        }
    
    except Exception as e:
        print(f"Upload error: {e}")
        return {
            'message': f'Error uploading video: {str(e)}',
            'error': True
        }


@app.delete('/videos/{video_name}')
async def delete_video(video_name: str):
    try:
        # Check if any resolution exists
        available_resolutions = r2_storage.get_available_resolutions(video_name)
        if not available_resolutions:
            raise HTTPException(status_code=404, detail=f"Video '{video_name}' not found")
        
        # Delete all resolutions
        success = r2_storage.delete_video_all_resolutions(video_name)
        
        if success:
            return JSONResponse(
                content={
                    'success': True,
                    'message': f"Video '{video_name}' and all resolutions deleted successfully"
                },
                status_code=200
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete video")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting video: {str(e)}")

