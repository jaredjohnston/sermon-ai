import logging
import tempfile
import os
from typing import BinaryIO, Optional, Dict, Any, Callable
from fastapi import UploadFile
import pytus
from app.config.settings import settings

logger = logging.getLogger(__name__)

class TUSUploadService:
    """
    INTERNAL SERVICE: TUS resumable uploads to Supabase Storage using SERVICE ROLE KEY
    
    WARNING: This service uses the service role key and should ONLY be used for:
    - Backend-to-Supabase uploads (system operations)
    - Server-side file processing
    
    DO NOT use this for user-initiated uploads from frontend!
    User uploads should use user JWT tokens directly with Supabase Storage API.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def _get_tus_endpoint(self) -> str:
        """Get the TUS endpoint URL for Supabase"""
        return f"{settings.SUPABASE_URL}/storage/v1/upload/resumable"
    
    def _get_tus_headers(self) -> Dict[str, str]:
        """
        Get headers required for TUS uploads to Supabase using SERVICE ROLE KEY
        WARNING: Only for internal backend operations!
        """
        return {
            'Authorization': f'Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}',
            'apikey': settings.SUPABASE_SERVICE_ROLE_KEY
        }
    
    async def upload_file_resumable(
        self,
        file: UploadFile,
        bucket_name: str,
        storage_path: str,
        content_type: str,
        chunk_size: int = 6 * 1024 * 1024,  # 6MB chunks as recommended
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Upload a file using TUS resumable upload protocol
        
        Args:
            file: FastAPI UploadFile object
            bucket_name: Supabase storage bucket name
            storage_path: Path where file will be stored
            content_type: MIME type of the file
            chunk_size: Size of each upload chunk (default 6MB)
            progress_callback: Optional callback for progress updates
            
        Returns:
            str: Public URL of the uploaded file
            
        Raises:
            Exception: If upload fails
        """
        temp_file_path = None
        
        try:
            self.logger.info(f"Starting TUS resumable upload for {storage_path}")
            
            # Create temporary file to store upload content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = temp_file.name
                
                # Copy uploaded file content to temporary file
                self.logger.info("Copying file content to temporary file...")
                file.file.seek(0)  # Ensure we're at the beginning
                while True:
                    chunk = file.file.read(chunk_size)
                    if not chunk:
                        break
                    temp_file.write(chunk)
                
                self.logger.info(f"Temporary file created: {temp_file_path}")
            
            # Prepare TUS upload parameters
            endpoint = self._get_tus_endpoint()
            headers = self._get_tus_headers()
            
            # Prepare metadata for Supabase
            metadata = {
                'bucketName': bucket_name,
                'objectName': storage_path,
                'contentType': content_type,
                'cacheControl': '3600'
            }
            
            self.logger.info(f"TUS endpoint: {endpoint}")
            self.logger.info(f"TUS metadata: {metadata}")
            
            # Start upload using pytus
            with open(temp_file_path, 'rb') as upload_file:
                self.logger.info("Starting TUS upload...")
                result = pytus.upload(
                    file_obj=upload_file,
                    tus_endpoint=endpoint,
                    chunk_size=chunk_size,
                    file_name=file.filename,
                    headers=headers,
                    metadata=metadata
                )
            
            self.logger.info(f"TUS upload completed successfully: {result}")
            
            # Generate public URL for the uploaded file
            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"
            
            return public_url
            
        except Exception as e:
            self.logger.error(f"TUS upload failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to upload file using TUS protocol: {str(e)}") from e
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    self.logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")
    
    async def upload_from_stream(
        self,
        file_stream: BinaryIO,
        bucket_name: str,
        storage_path: str,
        content_type: str,
        file_size: int,
        file_name: str = "stream_upload",
        chunk_size: int = 6 * 1024 * 1024,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Upload from a file-like object using TUS resumable upload
        
        Args:
            file_stream: File-like object to read from
            bucket_name: Supabase storage bucket name
            storage_path: Path where file will be stored
            content_type: MIME type of the file
            file_size: Total size of the file in bytes
            file_name: Name of the file for upload metadata
            chunk_size: Size of each upload chunk (default 6MB)
            progress_callback: Optional callback for progress updates
            
        Returns:
            str: Public URL of the uploaded file
        """
        try:
            self.logger.info(f"Starting TUS stream upload for {storage_path} ({file_size} bytes)")
            
            # Prepare TUS upload parameters
            endpoint = self._get_tus_endpoint()
            headers = self._get_tus_headers()
            
            # Prepare metadata for Supabase
            metadata = {
                'bucketName': bucket_name,
                'objectName': storage_path,
                'contentType': content_type,
                'cacheControl': '3600'
            }
            
            self.logger.info(f"TUS endpoint: {endpoint}")
            self.logger.info(f"TUS metadata: {metadata}")
            
            # Start upload using pytus directly from stream
            file_stream.seek(0)
            self.logger.info("Starting TUS stream upload...")
            result = pytus.upload(
                file_obj=file_stream,
                tus_endpoint=endpoint,
                chunk_size=chunk_size,
                file_name=file_name,
                headers=headers,
                metadata=metadata
            )
            
            self.logger.info(f"TUS stream upload completed successfully: {result}")
            
            # Generate public URL for the uploaded file
            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"
            
            return public_url
            
        except Exception as e:
            self.logger.error(f"TUS stream upload failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to upload stream using TUS protocol: {str(e)}") from e
    
    def should_use_resumable_upload(self, file_size: int, threshold: int = 6 * 1024 * 1024) -> bool:
        """
        Determine if resumable upload should be used based on file size
        
        Args:
            file_size: Size of the file in bytes
            threshold: Size threshold in bytes (default 6MB)
            
        Returns:
            bool: True if resumable upload should be used
        """
        return file_size > threshold

# Create singleton instance
tus_upload_service = TUSUploadService()