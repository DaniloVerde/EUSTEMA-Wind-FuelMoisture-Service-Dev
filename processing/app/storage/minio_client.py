from minio import Minio
from ..config import get_logger
from ..config.settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET

# Get module logger
logger = get_logger(__name__)

class MinioClient:
    def __init__(self):
        logger.info(f"Initializing MinIO client with endpoint: {MINIO_ENDPOINT}")
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False  # Set to True if using HTTPS
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure that the configured bucket exists, creating it if necessary"""
        try:
            if not self.client.bucket_exists(MINIO_BUCKET):
                logger.info(f"Bucket '{MINIO_BUCKET}' does not exist, creating it")
                self.client.make_bucket(MINIO_BUCKET)
                logger.info(f"Bucket '{MINIO_BUCKET}' created successfully")
            else:
                logger.debug(f"Bucket '{MINIO_BUCKET}' already exists")
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {str(e)}")
            raise
    
    def upload_file(self, file_path, object_name):
        """
        Upload a file to MinIO
        
        Args:
            file_path: Path to the local file
            object_name: Name to be used for the object in MinIO
            
        Returns:
            URL of the uploaded object
        """
        try:
            logger.info(f"Uploading file {file_path} to MinIO as {object_name}")
            self.client.fput_object(MINIO_BUCKET, object_name, file_path)
            url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{object_name}"
            logger.info(f"File uploaded successfully to {url}")
            return url
        except Exception as e:
            logger.error(f"Error uploading file to MinIO: {str(e)}")
            raise
    
    def download_file(self, object_name, file_path):
        """
        Download a file from MinIO
        
        Args:
            object_name: Name of the object in MinIO
            file_path: Path where to save the downloaded file
        """
        try:
            logger.info(f"Downloading object {object_name} from MinIO to {file_path}")
            self.client.fget_object(MINIO_BUCKET, object_name, file_path)
            logger.info(f"File downloaded successfully to {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file from MinIO: {str(e)}")
            raise
        
    def list_files(self, prefix=""):
        """
        List files in the bucket with an optional prefix
        
        Args:
            prefix: Optional prefix to filter objects
            
        Returns:
            List of object names
        """
        try:
            logger.debug(f"Listing objects in bucket '{MINIO_BUCKET}' with prefix '{prefix}'")
            objects = self.client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)
            object_names = [obj.object_name for obj in objects]
            logger.debug(f"Found {len(object_names)} objects")
            return object_names
        except Exception as e:
            logger.error(f"Error listing files in MinIO: {str(e)}")
            raise
