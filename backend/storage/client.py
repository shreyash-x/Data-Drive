from minio import Minio

from config import MINIO_CONFIG

minio_client = Minio(
    MINIO_CONFIG["host"],
    MINIO_CONFIG["username"],
    MINIO_CONFIG["password"],
    secure=False,
)
