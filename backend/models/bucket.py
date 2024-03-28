from mongoengine import (
    Document,
    StringField,
    ReferenceField,
    IntField,
    EnumField
)
from models.user import User
from models.common import Role,Permission
from config import app_config
"""
    this is the main bucket object model that we use
    stores the bucket that we have in the system
"""
class Bucket(Document):
    """
        Database model for storing the bucket information. 
    """
    name = StringField(required=True, unique=True)
    meta = {
        "indexes": [
            "name",
        ]
    }

"""
    this model is used to store accesses for the user to the bucket
"""
class BucketAccessList(Document):
    """
        Database model for storing the bucket access information. 
    """
    bucket = ReferenceField(Bucket, required=True)
    user = ReferenceField(User, required=True)
    role = EnumField(Role, default=Role.USER)
    permission = EnumField(Permission, default=Permission.NONE)
    storage_quota = IntField(required=True,default = app_config.default_user_quota)
    storage_used = IntField(required=True, default=0)
    
    meta = {
        "indexes": [
            "bucket",
            "user",
        ]
    }
    