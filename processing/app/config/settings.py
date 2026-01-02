import os

# API settings
ROOT_PATH = os.getenv("ROOT_PATH", "/")
DOCS_URL = os.getenv("DOCS_URL", "/docs")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS")
if not CORS_ALLOW_ORIGINS:
    raise RuntimeError("CORS_ALLOW_ORIGINS environment variable is not set or empty.")
CORS_ALLOW_ORIGINS = [origin.strip() for origin in CORS_ALLOW_ORIGINS.split(",")]

# MinIO settings
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cu68")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "False").lower() == "true"
MINIO_FORECAST_BUCKET = os.getenv("MINIO_FORECAST_BUCKET", "forecast-data")

if not all([MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY]):
    raise RuntimeError("MinIO credentials are not set in environment variables.")

# FEWS MinIO settings (optional; validated only when used)
FEWS_MINIO_ENDPOINT = os.getenv("FEWS_MINIO_ENDPOINT") or MINIO_ENDPOINT
FEWS_MINIO_ACCESS_KEY = os.getenv("FEWS_MINIO_ACCESS_KEY")
FEWS_MINIO_SECRET_KEY = os.getenv("FEWS_MINIO_SECRET_KEY")
FEWS_MINIO_USE_SSL = os.getenv("FEWS_MINIO_USE_SSL", os.getenv("MINIO_USE_SSL", "False")).lower() == "true"
FEWS_MINIO_BUCKET = os.getenv("FEWS_MINIO_BUCKET")
FEWS_MINIO_FORECAST_BUCKET = os.getenv("FEWS_MINIO_FORECAST_BUCKET")

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "windninja-results")
KAFKA_TOPIC_RESULTS = "dxc-sim-{cu}"
KAFKA_SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
KAFKA_SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM", "")
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")
KAFKA_SESSION_TIMEOUT_MS = int(os.getenv("KAFKA_SESSION_TIMEOUT_MS", "6000"))
KAFKA_REQUEST_TIMEOUT_MS = int(os.getenv("KAFKA_REQUEST_TIMEOUT_MS", "10000"))
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "")

if not all([KAFKA_USERNAME, KAFKA_PASSWORD]):
    raise RuntimeError("Kafka credentials are not set in environment variables.")

# WindNinja settings
WINDNINJA_EXECUTABLE = "WindNinja_cli"
DATA_DIR = "/data"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("LOG_FILE", "/app/logs/windninja.log")
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10 MB

# Log read/download settings
try:
    LOG_TAIL_DEFAULT_LINES = int(os.getenv("LOG_TAIL_DEFAULT_LINES", "50"))
except ValueError:
    LOG_TAIL_DEFAULT_LINES = 50