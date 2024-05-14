from mongoengine import (
    Document,
    StringField,
    ReferenceField,
    IntField,
    EnumField,
    ListField,
    BooleanField
)
from models.user import User
from models.common import Role,Permission
from config import app_config

from enum import Enum


class BucketType(Enum):
    DEFAULT = 0
    CHALLENGE = 1
    VIEWER = 2
    # ASSIGNMENT = 3
    # PAPER = 4
    # PROTOTYPE = 5

"""
    this is the main bucket object model that we use
    stores the bucket that we have in the system
"""
class Bucket(Document):
    """
        Database model for storing the bucket information. 
    """
    name = StringField(required=True, unique=True)
    bucket_type = EnumField(BucketType, default=BucketType.DEFAULT)
    meta = {
        "indexes": [
            "name",
            "bucket_type"
        ]
    }
    def __str__(self):
        return self.name
    def is_personal_space(self):
        return self.bucket_type == BucketType.DEFAULT or self.bucket_type == BucketType.CHALLENGE or self.bucket_type == BucketType.VIEWER
    def is_group_space(self):
        return self.bucket_type == BucketType.DEFAULT  or self.bucket_type == BucketType.VIEWER

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
    
class GroupAccessList(Document):
    """
        Database model for maintaining, user list and their corresponding accesses to the groups.
    """
    user = ReferenceField(User, required=True)
    bucket = ReferenceField(Bucket, required=True)
    group_name = StringField(required=True)
    path = StringField(required=True, unique=False)
    permission = EnumField(Permission, required=True, default=Permission.WRITE)
    meta = {
        "indexes": [
            "bucket",
            "group_name",
            "path",
            "user",
        ]
    }
    