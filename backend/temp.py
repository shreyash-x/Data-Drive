from models.user import User, AccessBuckets
def create_bucket():
    print("Creating Bucket")
    user = User.objects(username="shreyashjain1007@gmail.com").first()
    print(user)
    buckets = AccessBuckets(
        username = user,
        bucket_name = "test-1"
    ).save()
create_bucket()
