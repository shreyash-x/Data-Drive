from datetime import datetime
from mongoengine import (
    Document,
    StringField,
    IntField,
    ReferenceField,
    EnumField,
    BooleanField,
    DateTimeField,
)

from models.common import Permission
from models.user import User


class File(Document):
    """
    Database model for a file object, here file is a generic term for both file and folder
    Path : Path of the file.
    Size : Size of the file.
    Owner : Owner/Creator of the file.
    is_dir : Weather file object represents a folder or file.

    Public : Public permission for the file/folder (read, write, none), Public permission is used when a file is
    accessed by a user either when the user is not the owner of the file or the file is not explicitly shared with
    the user.
    """

    path = StringField(required=True, unique=True)
    size = IntField(required=True, default=0)
    last_modified = DateTimeField(required=True, default=datetime.now)
    owner = ReferenceField(User, required=True)
    is_dir = BooleanField(required=True, default=False)

    public = EnumField(Permission, required=True, default=Permission.NONE)

    meta = {
        "indexes": [
            "path",
        ]
    }

    def get_permission(self, user):
        """
        Get the access permission for a user for a file.
        """
        if self.owner == user:
            return min(Permission.WRITE, user.permission)

        shared_file = SharedFile.objects(file=self, user=user).first()
        if shared_file:
            return shared_file.permission

        return self.public

    def can_write(self, user):
        """
        Check if a user has write permission for a file.
        """
        return self.get_permission(user) == Permission.WRITE

    def can_read(self, user):
        """
        Check if a user has read permission for a file.
        """
        return self.get_permission(user) in [Permission.WRITE, Permission.READ]

    def get_size(self):
        if not self.is_dir:
            return self.size

        pipeline = [
            {"$match": {"path": {"$regex": f"^{self.path}/"}}},
            {"$group": {"_id": None, "size": {"$sum": "$size"}}},
        ]

        result = File.objects.aggregate(*pipeline)
        return result.next()["size"]

    def get_last_modified(self):
        if not self.is_dir:
            return self.last_modified

        pipeline = [
            {"$match": {"path": {"$regex": f"^{self.path}/"}}},
            {"$sort": {"last_modified": -1}},
            {"$limit": 1},
        ]

        result = File.objects.aggregate(*pipeline)
        return result.next()["last_modified"]


class SharedFile(Document):
    """
    Database model for a shared file object, here file is a generic term for both file and folder.
    File : Reference to the file object that is shared.
    User : Reference to the user object with whom the file is shared.
    Permission : Permission granted to the user for the file.
    Owner : Owner of the file.
    Explicit : Weather the file is explicitly shared with the user or the user has access to the file because of a
    parent folder that is explicitly shared with
    the user.
    """

    file = ReferenceField(File, required=True)
    user = ReferenceField(User, required=True)
    permission = EnumField(Permission, required=True)
    explicit = BooleanField(required=True, default=False)
    owner = ReferenceField(User, required=True)

    meta = {
        "indexes": [
            "file",
            "user",
            "owner",
        ]
    }
