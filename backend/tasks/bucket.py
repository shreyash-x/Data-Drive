import io
from storage.client import minio_client as mc

# Create a bucket in minio
def create_bucket_helper(bucket_name):
    bucket = mc.make_bucket(bucket_name)
    create_folder_helper(bucket_name, bucket_name)
    return bucket

# Create empty folder in minio
def create_folder_helper(bucket_name, folder_path):
    mc.put_object(bucket_name, folder_path + "/_", io.BytesIO(b""), 0)
    return