from storage.client import minio_client as mc

# Create a bucket in minio
def create_bucket_helper(bucket_name):
    bucket = mc.make_bucket(bucket_name)
    return bucket