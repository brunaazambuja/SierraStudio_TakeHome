import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os
from typing import List, Dict, Optional


class CloudflareR2Storage:
    def __init__(self, account_id: str, access_key_id: str, secret_access_key: str, bucket_name: str):
        self.bucket_name = bucket_name
        self.account_id = account_id
        
        endpoint_url = f'https://{account_id}.r2.cloudflarestorage.com'
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
    
    def upload_video(self, file_content: bytes, filename: str, content_type: str = 'video/mp4') -> bool:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'uploaded-by': 'sierra-video-app'
                }
            )
            return True
        except ClientError as e:
            print(f"Error uploading to R2: {e}")
            return False
    
    def upload_image(self, file_content: bytes, filename: str, content_type: str = 'image/jpeg') -> bool:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_content,
                ContentType=content_type,
                CacheControl='public',  
                Metadata={
                    'uploaded-by': 'sierra-video-app'
                }
            )
            return True
        except ClientError as e:
            print(f"Error uploading image to R2: {e}")
            return False
    
    def list_videos(self) -> List[Dict]:
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            videos = []
            
            if 'Contents' not in response:
                return videos
            
            for obj in response['Contents']:
                videos.append({
                    'name': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'id': obj['Key']  
                })
            
            videos.sort(key=lambda x: x['last_modified'], reverse=True)
            return videos
            
        except ClientError as e:
            print(f"Error listing R2 objects: {e}")
            return []
    
    def get_asset_url(self, filename: str) -> str:
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={ 'Bucket': self.bucket_name, 'Key': filename },
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return ""
    
    def delete_video(self, filename: str) -> bool:
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return True
        except ClientError as e:
            print(f"Error deleting from R2: {e}")
            return False
    
    def asset_exists(self, filename: str) -> bool:
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return True
        except ClientError:
            return False
    
    def get_video_metadata(self, filename: str) -> Optional[Dict]:
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return {
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'].isoformat(),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            print(f"Error getting metadata: {e}")
            return None
    
    def upload_video_resolutions(self, video_data: Dict[str, bytes], base_filename: str, content_type: str = 'video/mp4') -> Dict[str, bool]:
        results = {}
        base_name = os.path.splitext(base_filename)[0]
        
        for resolution, content in video_data.items():
            filename = f"{base_name}_{resolution}.mp4"
            
            try:
                success = self.upload_video(content, filename, content_type)
                results[resolution] = success
                if success:
                    print(f"Uploaded {resolution} version: {filename}")
                else:
                    print(f"Failed to upload {resolution} version")
            except Exception as e:
                print(f"Error uploading {resolution}: {e}")
                results[resolution] = False
        
        return results
    
    def get_available_resolutions(self, base_filename: str) -> List[str]:
        base_name = os.path.splitext(base_filename)[0]
        for res in ['_360p', '_720p', '_1080p', '_original']:
            if base_name.endswith(res):
                base_name = base_name[:-len(res)]
                break
        
        resolutions = []
        for res in ['360p', '720p', '1080p', 'original']:
            filename = f"{base_name}_{res}.mp4"
            if self.asset_exists(filename):
                resolutions.append(res)
        
        return resolutions
    
    def get_video_url_by_resolution(self, base_filename: str, resolution: str = '720p') -> str:
        base_name = os.path.splitext(base_filename)[0]
        for res in ['_360p', '_720p', '_1080p', '_original']:
            if base_name.endswith(res):
                base_name = base_name[:-len(res)]
                break
        
        filename = f"{base_name}_{resolution}.mp4"
        if self.asset_exists(filename):
            return self.get_asset_url(filename)
        return ""
    
    def list_videos_grouped(self) -> List[Dict]:
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return []
            
            video_groups = {}
            
            for obj in response['Contents']:
                key = obj['Key']
                
                # Skip images
                if key.endswith('_poster.jpg') or key.endswith('_thumbnail_strip.png'):
                    continue
                
                base_name = os.path.splitext(key)[0]
                resolution = None
                
                for res in ['_360p', '_720p', '_1080p', '_original']:
                    if base_name.endswith(res):
                        resolution = res[1:]  # Remove underscore
                        base_name = base_name[:-len(res)]
                        break
                
                if base_name not in video_groups:
                    video_groups[base_name] = {
                        'base_name': base_name,
                        'display_name': base_name,
                        'resolutions': [],
                        'size': 0,
                        'last_modified': obj['LastModified'],
                        'last_modified_iso': obj['LastModified'].isoformat(),
                        'files': [],
                        'poster_url': None,
                        'thumbnail_strip_url': None
                    }
                
                video_groups[base_name]['resolutions'].append(resolution)
                video_groups[base_name]['files'].append(key)
                # use the largest file size for display
                if obj['Size'] > video_groups[base_name]['size']:
                    video_groups[base_name]['size'] = obj['Size']
                # use the most recent modification time
                if obj['LastModified'] > video_groups[base_name]['last_modified']:
                    video_groups[base_name]['last_modified'] = obj['LastModified']
                    video_groups[base_name]['last_modified_iso'] = obj['LastModified'].isoformat()
            
            # poster and thumbnail URLs
            for base_name, video_data in video_groups.items():
                # poster image
                poster_key = f"{base_name}_poster.jpg"
                if self.asset_exists(poster_key):
                    video_data['poster_url'] = self.get_asset_url(poster_key)
                
                # thumbnail strip
                thumbnail_key = f"{base_name}_thumbnail_strip.png"
                if self.asset_exists(thumbnail_key):
                    video_data['thumbnail_strip_url'] = self.get_asset_url(thumbnail_key)
            
            # sorting
            videos = list(video_groups.values())
            videos.sort(key=lambda x: x['last_modified'], reverse=True)
            
            # last_modified datetime to ISO string for JSON serialization
            for video in videos:
                video['last_modified'] = video.pop('last_modified_iso')
            
            return videos
            
        except ClientError as e:
            print(f"Error listing R2 objects: {e}")
            return []
    
    def delete_video_all_resolutions(self, base_filename: str) -> bool:
        base_name = os.path.splitext(base_filename)[0]
        for res in ['_360p', '_720p', '_1080p', '_original']:
            if base_name.endswith(res):
                base_name = base_name[:-len(res)]
                break
        
        deleted = False
        
        for res in ['360p', '720p', '1080p', 'original']:
            filename = f"{base_name}_{res}.mp4"
            if self.asset_exists(filename):
                success = self.delete_video(filename)
                if success:
                    deleted = True
                    print(f"Deleted {res} version")
        
        # poster image
        poster_filename = f"{base_name}_poster.jpg"
        if self.asset_exists(poster_filename):
            success = self.delete_video(poster_filename)
            if success:
                deleted = True
                print(f"Deleted poster image")
        
        # thumbnail strip
        thumbnail_filename = f"{base_name}_thumbnail_strip.png"
        if self.asset_exists(thumbnail_filename):
            success = self.delete_video(thumbnail_filename)
            if success:
                deleted = True
                print(f"Deleted thumbnail strip")
        
        return deleted

