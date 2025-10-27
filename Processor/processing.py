import cv2
import tempfile
import os
from typing import Tuple, Dict, Optional
import ffmpeg
from io import BytesIO
from PIL import Image


class VideoValidator:
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4','.mov', '.webm'}
    SUPPORTED_MIME_TYPES = {'video/mp4', 'video/quicktime', 'video/webm'}
   
    @staticmethod
    def is_video_file(filename: str, content_type: str = None) -> bool:
        _, ext = os.path.splitext(filename.lower())
        has_valid_extension = ext in VideoValidator.SUPPORTED_VIDEO_EXTENSIONS
        
        has_valid_mime = True
        if content_type:
            has_valid_mime = content_type.lower() in VideoValidator.SUPPORTED_MIME_TYPES or \
                           content_type.lower().startswith('video/')
        
        return has_valid_extension and has_valid_mime
    
    @staticmethod
    def check_if_video_is_corrupted_opencv(video_content: bytes) -> Tuple[bool, Dict]:
        # Create a temporary file to save the video
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_path = temp_file.name
            temp_file.write(video_content)
        
        try:
            cap = cv2.VideoCapture(temp_path)
            
            if not cap.isOpened():
                return False, {'error': 'Unable to open video file', 'corrupted': True}
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Check if basic properties are valid
            if frame_count <= 0 or fps <= 0 or width <= 0 or height <= 0:
                return False, {
                    'error': 'Invalid video properties',
                    'corrupted': True,
                    'frame_count': frame_count,
                    'fps': fps,
                    'resolution': f'{width}x{height}'
                }
            
            # Try to read some frames to check for corruption
            frames_to_check = min(10, frame_count) 
            readable_frames = 0
            
            for _ in range(frames_to_check):
                ret, frame = cap.read()
                if ret and frame is not None:
                    readable_frames += 1
                else:
                    break
            
            cap.release()
            
            # if readable_frames = 0, the video is corrupted
            if readable_frames == 0:
                return False, {
                    'error': 'Unable to read video frames',
                    'corrupted': True,
                    'frame_count': frame_count,
                    'fps': fps,
                    'resolution': f'{width}x{height}'
                }
            
            return True, {
                'corrupted': False,
                'frame_count': frame_count,
                'fps': round(fps, 2),
                'resolution': f'{width}x{height}',
                'duration_seconds': round(duration, 2),
                'readable_frames': readable_frames,
                'checked_frames': frames_to_check
            }
            
        except Exception as e:
            return False, {'error': f'Error processing video: {str(e)}', 'corrupted': True}
        
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    @staticmethod
    def validate_video(filename: str, content_type: str, video_content: bytes, max_size_mb: int = 50) -> Tuple[bool, str, Dict]:
        if not VideoValidator.is_video_file(filename, content_type):
            return False, 'File is not a supported video format', {}
        
        # MB -> bytes
        max_size_bytes = max_size_mb * 1024 * 1024
        file_size_mb = len(video_content) / (1024 * 1024)
        
        if len(video_content) < 0:
            return False, 'Video file is empty', {}
        
        if len(video_content) > max_size_bytes:
            return False, f'Video file is too large. Maximum size: {max_size_mb}MB. Your file: {file_size_mb}MB', {}
        
        is_valid, details = VideoValidator.check_if_video_is_corrupted_opencv(video_content)
        
        if not is_valid:
            error_msg = details.get('error', 'Video file is corrupted')
            return False, error_msg, details
        
        details['file_size_mb'] = round(file_size_mb, 2)
        return True, 'Video is valid', details


class VideoTranscoder:
    RESOLUTIONS = {
        '360p': {'width': 640, 'height': 360, 'bitrate': '800k'},
        '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k'},
        '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k'}
    }
    
    @staticmethod
    def get_video_resolution(video_path: str) -> Tuple[int, int]:
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if video_stream:
                width = int(video_stream['width'])
                height = int(video_stream['height'])
                return width, height
            return 0, 0
        except Exception as e:
            print(f"Error getting video resolution: {e}")
            return 0, 0
    
    @staticmethod
    def transcode_video(input_path: str, output_path: str, resolution: str) -> bool:
        #Transcode a video to a specific resolution
        try:
            if resolution not in VideoTranscoder.RESOLUTIONS:
                print(f"Invalid resolution: {resolution}")
                return False
            
            config = VideoTranscoder.RESOLUTIONS[resolution]
            width = config['width']
            height = config['height']
            bitrate = config['bitrate']
            
            orig_width, orig_height = VideoTranscoder.get_video_resolution(input_path)
            
            if orig_height > 0 and orig_height < height:
                width = orig_width
                height = orig_height
            
            # Build ffmpeg script
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec='libx264',
                acodec='aac',
                video_bitrate=bitrate,
                audio_bitrate='128k',
                vf=f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
                preset='medium',
                crf=23,
                movflags='faststart',
                f='mp4'
            )
            
            # run script
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            return True
            
        except ffmpeg.Error as e:
            print(f"FFmpeg error transcoding to {resolution}: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            print(f"Error transcoding to {resolution}: {e}")
            return False
    
    @staticmethod
    def transcode_to_multiple_resolutions(input_content: bytes) -> Dict[str, bytes]:
        results = {}
        temp_input = None
        temp_outputs = []
        resolutions = resolutions = list(VideoTranscoder.RESOLUTIONS.keys())
        
        try:
            # create temporary input file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_input = temp_file.name
                temp_file.write(input_content)
            
            # get original resolution to avoid unnecessary upscaling
            orig_width, orig_height = VideoTranscoder.get_video_resolution(temp_input)
            print(f"Original video resolution: {orig_width}x{orig_height}")
            
            # Transcode to each resolution
            for resolution in resolutions:
                temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{resolution}.mp4')
                temp_output_path = temp_output.name
                temp_output.close()
                temp_outputs.append(temp_output_path)
                
                print(f"Transcoding to {resolution}...")
                success = VideoTranscoder.transcode_video(temp_input, temp_output_path, resolution)
                
                if success and os.path.exists(temp_output_path):
                    with open(temp_output_path, 'rb') as f:
                        results[resolution] = f.read()
                    print(f"Successfully transcoded to {resolution}")
                else:
                    print(f"Failed to transcode to {resolution}")
        except Exception as e:
            print(f"Error in multi-resolution transcoding: {e}")
        
        finally:
            if temp_input and os.path.exists(temp_input):
                try:
                    os.unlink(temp_input)
                except:
                    pass
            
            for temp_output in temp_outputs:
                if os.path.exists(temp_output):
                    try:
                        os.unlink(temp_output)
                    except:
                        pass
        
        return results


class ThumbnailGenerator:
    @staticmethod
    def generate_poster(video_content: bytes, time_position: float = 3.0) -> Optional[bytes]:
        temp_video_path = None
        
        try:
            # Save video to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_video_path = temp_file.name
                temp_file.write(video_content)
            
            cap = cv2.VideoCapture(temp_video_path)
            
            if not cap.isOpened():
                print("Failed to open video for poster generation")
                return None
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            if time_position > duration:
                time_position = duration / 2
            
            # Seek to the desired time
            frame_number = int(time_position * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                print("Failed to read frame for poster")
                return None
            
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            
            max_width = 1280
            if pil_image.width > max_width:
                aspect_ratio = pil_image.height / pil_image.width
                new_height = int(max_width * aspect_ratio)
                pil_image = pil_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to JPEG bytes
            buffer = BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85, optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error generating poster: {e}")
            return None
            
        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                except:
                    pass
    
    @staticmethod
    def generate_thumbnail_strip(video_content: bytes, num_thumbnails: int = 10, 
                                 strip_width: int = 160) -> Optional[bytes]:
        temp_video_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_video_path = temp_file.name
                temp_file.write(video_content)
            
            cap = cv2.VideoCapture(temp_video_path)
            
            if not cap.isOpened():
                print("Failed to open video for thumbnail strip generation")
                return None
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            if duration <= 0 or frame_count <= 0:
                return None
            
            # Calculate frame intervals
            interval = duration / (num_thumbnails + 1)  # +1 to avoid first and last second
            
            thumbnails = []
            
            for i in range(num_thumbnails):
                # Calculate time position for this thumbnail
                time_pos = interval * (i + 1)
                frame_number = int(time_pos * fps)
                
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Resize thumbnail to specified width
                    aspect_ratio = pil_image.height / pil_image.width
                    thumb_height = int(strip_width * aspect_ratio)
                    pil_image = pil_image.resize((strip_width, thumb_height), Image.Resampling.LANCZOS)
                    
                    thumbnails.append(pil_image)
            
            cap.release()
            
            if not thumbnails:
                print("No thumbnails generated")
                return None
            
            # Create horizontal strip
            total_width = strip_width * len(thumbnails)
            max_height = max(thumb.height for thumb in thumbnails)
            
            # Create blank canvas
            strip = Image.new('RGB', (total_width, max_height), color='black')
            
            # Paste thumbnails side by side
            x_offset = 0
            for thumb in thumbnails:
                # Center vertically if heights differ
                y_offset = (max_height - thumb.height) // 2
                strip.paste(thumb, (x_offset, y_offset))
                x_offset += strip_width
            
            # Convert to PNG bytes
            buffer = BytesIO()
            strip.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error generating thumbnail strip: {e}")
            return None
            
        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                except:
                    pass