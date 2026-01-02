from typing import Optional

from minio import Minio
from ..config import get_logger
from ..config.settings import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    MINIO_USE_SSL,
    MINIO_FORECAST_BUCKET,
    FEWS_MINIO_ENDPOINT,
    FEWS_MINIO_ACCESS_KEY,
    FEWS_MINIO_SECRET_KEY,
    FEWS_MINIO_BUCKET,
    FEWS_MINIO_USE_SSL,
    FEWS_MINIO_FORECAST_BUCKET,
)

# Get module logger
logger = get_logger(__name__)


class _BaseMinioClient:
    def __init__(
        self,
        *,
        endpoint: Optional[str],
        access_key: Optional[str],
        secret_key: Optional[str],
        use_ssl: bool,
        bucket: Optional[str],
        forecast_bucket=None,
        client_name: str = "MinIO",
    ):
        if not endpoint:
            raise RuntimeError(f"{client_name} endpoint is not configured")
        if not access_key or not secret_key:
            raise RuntimeError(f"{client_name} credentials are not configured")
        if not bucket:
            raise RuntimeError(f"{client_name} bucket is not configured")

        self.endpoint = endpoint
        self.bucket = bucket
        self.forecast_bucket = forecast_bucket or bucket

        logger.info(f"Initializing {client_name} client with endpoint: {endpoint}")
        self.client = Minio(
            endpoint,  # type: ignore
            access_key=access_key,
            secret_key=secret_key,
            secure=use_ssl,
        )

        self._ensure_bucket_exists(self.bucket)
        if self.forecast_bucket != self.bucket:
            self._ensure_bucket_exists(self.forecast_bucket)

    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure that the bucket exists, creating it if necessary."""
        try:
            if not self.client.bucket_exists(bucket_name):
                logger.info(f"Bucket '{bucket_name}' does not exist, creating it")
                self.client.make_bucket(bucket_name)
                logger.info(f"Bucket '{bucket_name}' created successfully")
            else:
                logger.debug(f"Bucket '{bucket_name}' already exists")
        except Exception as e:
            logger.error(f"Error ensuring bucket exists '{bucket_name}': {str(e)}")
            raise

    def _normalize_metadata(self, d):
        out = {}
        for k, v in d.items():
            key = str(k).strip().lower()
            key = key.replace(" ", "_")
            out[key] = str(v)
        return out

    def upload_file(self, file_path, object_name, dict_headers={}):
        normalized_headers = self._normalize_metadata(dict_headers)

        try:
            logger.info(f"Uploading file {file_path} to MinIO as {object_name}")
            self.client.fput_object(self.bucket, object_name, file_path, metadata=normalized_headers)
            url = f"{self.endpoint}/{self.bucket}/{object_name}"
            logger.info(f"File uploaded successfully to {url}")
            return url
        except Exception as e:
            logger.error(f"Error uploading file to MinIO: {str(e)}")
            raise

    def download_file(self, object_name, file_path, is_forecast=False):
        try:
            bucket_name = self.forecast_bucket if is_forecast is True else self.bucket
            logger.info(f"Downloading object {object_name} from MinIO to {file_path}")
            self.client.fget_object(bucket_name, object_name, file_path)
            logger.info(f"File downloaded successfully to {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file from MinIO: {str(e)}")
            raise

class MinioClient:
    def __init__(self):
        self._client = _BaseMinioClient(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            use_ssl=MINIO_USE_SSL,
            bucket=MINIO_BUCKET,
            forecast_bucket=MINIO_FORECAST_BUCKET,
            client_name="MinIO",
        )

    def upload_file(self, file_path, object_name, dict_headers={}):
        return self._client.upload_file(file_path, object_name, dict_headers=dict_headers)

    def download_file(self, object_name, file_path, is_forecast=False):
        return self._client.download_file(object_name, file_path, is_forecast=is_forecast)


class FewsMinioClient:
    def __init__(self):
        if not FEWS_MINIO_BUCKET:
            raise RuntimeError("FEWS_MINIO_BUCKET environment variable is not set")
        if not FEWS_MINIO_FORECAST_BUCKET:
            raise RuntimeError("FEWS_MINIO_FORECAST_BUCKET environment variable is not set")
        if not FEWS_MINIO_ACCESS_KEY or not FEWS_MINIO_SECRET_KEY:
            raise RuntimeError("FEWS MinIO credentials are not set in environment variables")

        self._client = _BaseMinioClient(
            endpoint=FEWS_MINIO_ENDPOINT,
            access_key=FEWS_MINIO_ACCESS_KEY,
            secret_key=FEWS_MINIO_SECRET_KEY,
            use_ssl=FEWS_MINIO_USE_SSL,
            bucket=FEWS_MINIO_BUCKET,
            forecast_bucket=FEWS_MINIO_FORECAST_BUCKET,
            client_name="FEWS MinIO",
        )

    def upload_file(self, file_path, object_name, dict_headers={}):
        return self._client.upload_file(file_path, object_name, dict_headers=dict_headers)

    def download_file(self, object_name, file_path, is_forecast=False):
        return self._client.download_file(object_name, file_path, is_forecast=is_forecast)
