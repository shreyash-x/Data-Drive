import os
import mimetypes
import io
import secrets
from datetime import datetime, timedelta
from typing import Annotated, List
import uuid


import minio.commonconfig
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Body,
    UploadFile,
    Form,
    BackgroundTasks,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from minio.deleteobjects import DeleteObject

from dependencies import get_auth_user, get_auth_user_optional, MessageResponse
from config import app_config, MINIO_BUCKET
from models.user import User,AccessBuckets
from models.file import File, SharedFile
from models.common import Permission, Task
from models.job import Job, Status
from models.bucket import Bucket,GroupAccessList
from storage.client import minio_client as mc
from tasks.files import create_job, clean_expired_jobs, upload_file_to_minio

# helper function to get bucket name and file path separately
from utils.files import getFilePath


files_router = APIRouter(
    prefix="",
    tags=["files"],
    responses={404: {"description": "Not found"}},
)


class PathForm(BaseModel):
    path: str


class ObjectModel(BaseModel):
    path: str
    is_dir: bool
    last_modified: datetime | None
    size: int | None
    metadata: dict | None
    bucket: str | None
    task_type: str


class SharedFileModel(BaseModel):
    path: str
    is_dir: bool
    last_modified: datetime | None
    size: int | None
    metadata: dict | None
    permission: Permission
    explicit: bool
    shared_with: str
    bucket: str | None


@files_router.post("/upload", response_model=MessageResponse)
async def upload_file(
    path: Annotated[str, Form()],
    file: UploadFile,
    username: Annotated[str, Depends(get_auth_user)],
    background_tasks: BackgroundTasks,
):
    """
    Upload a file to the specified path.

    This function performs the following checks:

        - Check if the file already exists.

        - Check if the parent directory exists.

        - Check if the user has write permission for the parent directory.

    Then it uploads the file to the specified path to the minio server and creates a database entry for the file in the
    mongo database. It also inherits the share permissions from the parent directory.

    Parameters:

        - **path**: Path to upload the file to.

        - **file**: File to upload.

    Returns:

        - **message**: Message indicating whether the file was uploaded successfully or not.
    """
    print("INSIDE UPloaD FUNCTIOn")
    fileObj = File.objects(path=path).first()
    if fileObj:
        raise HTTPException(status_code=400, detail="File already exists!")

    directory = File.objects(path=os.path.dirname(path)).first()
    if not directory:
        raise HTTPException(status_code=400, detail="Directory does not exist!")

    user = User.objects(username=username).first()
    if not directory.can_write(user):
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to upload to this directory!",
        )

    file_ext = os.path.splitext(file.filename)[1]
    ALLOWED_FILE_EXTENSIONS = app_config.allowed_file_extensions
    if ALLOWED_FILE_EXTENSIONS and file_ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed!")
        # return {"message": "File type not allowed!"}

    content_type = mimetypes.guess_type(path)[0]
    if content_type is None:
        content_type = "application/octet-stream"

    # Get quota user
    quota_user = User.objects(username=username).first()
    if quota_user.storage_used + file.size > quota_user.storage_quota:
        raise HTTPException(status_code=400, detail="User storage quota exceeded!")

    try:
        background_tasks.add_task(
            upload_file_to_minio, path, file, content_type, quota_user, directory
        )

        return {"message": "File uploaded successfully!"}

    except Exception as err:
        print(err)
        raise HTTPException(status_code=400, detail=str(err))


@files_router.post("/mkdir", response_model=MessageResponse)
def mkdir(
    data: Annotated[PathForm, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user)],
):
    """
    Create a directory at the specified path.

    This function performs the following checks:

        - Check if the directory already exists.

        - Check if the parent directory exists.

        - Check if the user has write permission for the parent directory.

    Then it creates a directory at the specified path on the minio server and creates a database entry for the directory.
    For directories, the minio server stores a dummy object with the name of the directory and a trailing underscore "_"
    since minio does not support empty directories.

    Parameters:

        - **path**: Path to create the directory at.

    Returns:

        - **message**: Message indicating whether the directory was created successfully or not.
    """
    directory = File.objects(path=data.path).first()
    if directory:
        return {"message": "Directory already exists!"}

    parent = File.objects(path=os.path.dirname(data.path)).first()
    if not parent:
        return {"message": "Parent directory does not exist!"}

    user = User.objects(username=username).first()
    if not parent.can_write(user):
        return {"message": "You do not have permission to create a directory here!"}

    directory = File(path=data.path, owner=user, is_dir=True, group_path=parent.group_path,parent_task_type=parent.parent_task_type).save()
    bucketName, filePath = getFilePath(data.path)
    mc.put_object(bucketName, filePath + "/_", io.BytesIO(b""), 0)
    return {"message": "Directory created successfully!"}


@files_router.post("/list", response_model=List[ObjectModel])
def list(
    data: Annotated[PathForm, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user_optional)],
):
    """
    List the files in the specified directory.

    This function performs the following checks:

        - Check if the directory exists.

        - Check if the user has read permission for the directory.

    Then it lists the files and folder in the specified directory on the minio server and their associated information
    including the path, whether it is a directory, last modified time, size and metadata.

    Parameters:

        - **path**: Path to list the files in.

    Returns:

        - List of files and folders in the specified directory.
    """
    print("DATA",data)
    print(data.path)
    directory = File.objects(path=data.path).first()
    print(directory)
    if not directory or not directory.is_dir:
        print("Directory does not exist!")
        raise HTTPException(status_code=400, detail="Directory does not exist!")

    if username:
        user = User.objects(username=username).first()
    else:
        user = None
    if not directory.can_read(user):
        print("You do not have permission to access this directory!")
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to access this directory!",
        )

    objJSON = []
    bucketName, filePath = getFilePath(data.path)
    
    bucket = Bucket.objects(name=bucketName).first()
    
    # def check_if_has_permission(obj, user):
    #     query_path = bucketName + '/' + obj.object_name
    #     # Remove the trailing '/'
    #     query_path = query_path[:-1] if query_path[-1] == '/' else query_path
        
    #     # Check if user has direct permission for the file
    #     if user.username in query_path:
    #         return True
        
    #     # Check if there's a group access entry for the file
    #     gf = GroupAccessList.objects(user=user, path=query_path).first()
    #     if gf:
    #         return True
        
    #     # Recursively check parent directories
    #     while True:
    #         # Get the parent directory path
    #         parent_path = os.path.dirname(query_path)
            
    #         # Check if we've reached the root directory
    #         if parent_path == query_path:
    #             break
            
    #         # Check if there's a group access entry for the parent directory
    #         gf = GroupAccessList.objects(user=user, path=parent_path).first()
    #         if gf:
    #             return True
            
    #         # Update query_path for the next iteration
    #         query_path = parent_path
    #     return False
    for obj in mc.list_objects(bucketName, filePath + "/", recursive=False):
        filePath = f"{bucketName}/{obj.object_name}"
        # remove the trailing '/'
        filePath = filePath[:-1] if filePath[-1] == '/' else filePath
        fileData = File.objects(path=filePath).first()
        print(f"{filePath} is being checked for permission")
        
        if fileData is not None and not fileData.can_read(user):
            continue
        print("<---->",filePath)
        objJSON.append(
            {
                "path": obj.object_name,
                "is_dir": obj.is_dir,
                "last_modified": obj.last_modified,
                "size": obj.size,
                "metadata": obj.metadata,
                "bucket": bucketName,
                "task_type": fileData.parent_task_type.name if fileData is not None else "NONE",
            }
        )

    return objJSON


class DuResponse(BaseModel):
    size: int
    last_modified: datetime | None


@files_router.get("/du/{path:path}", response_model=DuResponse)
def du(
    path: str,
    username: Annotated[str, Depends(get_auth_user_optional)],
):
    directory = File.objects(path=path).first()
    if not directory or not directory.is_dir:
        raise HTTPException(status_code=400, detail="Directory does not exist!")

    if username:
        user = User.objects(username=username).first()
    else:
        user = None
    if not directory.can_read(user):
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to access this directory!",
        )
    try:
        return {
            "size": directory.get_size(),
            "last_modified": directory.get_last_modified(),
        }
    except Exception as err:
        # raise HTTPException(status_code=400, detail=str(err))
        print("Accessing empty directory")
        return {
            "size": 0,
            "last_modified": None,
        }



@files_router.post("/delete", response_model=MessageResponse)
def delete(
    data: Annotated[PathForm, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user)],
):
    """
    Delete the file/folder specified by the path.

    This function performs the following checks:

        - Check if the file/folder exists.

        - Check if user is trying to delete their home directory.

        - Check if the user has write permission for the file/folder.

    Then it deletes the file/folder specified by the path on the minio server and deletes the file database entries and
    share database entries associated with the file/folder. If the file/folder is a directory, it also deletes all the
    files and folders inside the directory.

    Parameters:

        - **path**: Path to delete the file/folder at.

    Returns:

        - **message**: Message indicating whether the file/folder was deleted successfully or not.
    """
    file = File.objects(path=data.path).first()
    if not file:
        raise HTTPException(status_code=400, detail="File does not exist!")

    is_dir = file.is_dir
    if is_dir:
        if file.path == username:
            raise HTTPException(
                status_code=400, detail="You cannot delete your home directory!"
            )

    user = User.objects(username=username).first()
    if not file.can_write(user):
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to delete this file/folder!",
        )
    quota_user = User.objects(username=data.path.split("/")[0]).first()
    bucketName, filePath = getFilePath(data.path)
    if is_dir:      
        mc.remove_object(bucketName, filePath + "/_")
        delete_object_list = map(
            lambda x: DeleteObject(x.object_name),
            mc.list_objects(bucketName, filePath, recursive=True),
        )
        errors = mc.remove_objects(bucketName, delete_object_list)
        # delete shared file objects associated with files in the directory
        for file in File.objects(path__startswith=data.path):
            SharedFile.objects(file=file).delete()
            quota_user.storage_used -= file.size
            file.delete()
        for error in errors:
            print("Error occurred when deleting " + error.object_name)
        quota_user.save()
        return {"message": "Folder deleted successfully!"}
    else:
        mc.remove_object(bucketName, filePath)
        SharedFile.objects(file=file).delete()
        quota_user.storage_used -= file.size
        file.delete()
        quota_user.save()
        return {"message": "File deleted successfully!"}


@files_router.get("/get/{path:path}", response_class=FileResponse)
def get_file(path: str, username: Annotated[str, Depends(get_auth_user_optional)], token: str = None):
    """
    Get the file specified by the path.

    This function performs the following checks:

        - Check if the file exists.

        - Check if the path points to a file and not a directory.

        - Check if the user has read permission for the file.

    Then it gets the file specified by the path from the minio server and returns it.
    """
    file = File.objects(path=path).first()
    if not file:
        raise HTTPException(status_code=400, detail="File does not exist!")

    if file.is_dir:
        raise HTTPException(status_code=400, detail="Cannot preview a directory!")

    if file.size > app_config.max_preview_size:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds maximum preview size!",
        )

    has_access = False
    if token is not None:
        sharedFile = SharedFile.objects(publicAccessToken=token).first()
        if not sharedFile:
            raise HTTPException(status_code=400, detail="Invalid token!")
        elif sharedFile.is_shared_public() is False:
            raise HTTPException(status_code=400, detail="File is not shared publicly!")
        elif sharedFile.check_expiration() is True:
            raise HTTPException(status_code=400, detail="File has expired!")
        else:
            if sharedFile.file.path == path:
                has_access = True

    user = None
    if username:
        user = User.objects(username=username).first()
    if not file.can_read(user) and not has_access:
        raise HTTPException(
            status_code=400, detail="You do not have permission to access this file!!"
        )

    try:
        bucketName, filePath = getFilePath(path)
        mc.fget_object(bucketName, filePath, "/tmp/" + path)
        return "/tmp/" + path
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@files_router.post("/get_public_file", response_class=FileResponse)
def get_public_file(
    token: Annotated[str, Body(embed=True)],
):
    """
    Get the file specified by the path.

    This function performs the following checks:

        - Check if the file exists.

        - Check if the path points to a file and not a directory.

        - Check if the user has read permission for the file.

    Then it gets the file specified by the path from the minio server and returns it.
    """
    sharedFile = SharedFile.objects(publicAccessToken=token).first()
    if not sharedFile:
        raise HTTPException(status_code=400, detail="Invalid token!")
    
    if sharedFile.is_shared_public() is False:
        raise HTTPException(status_code=400, detail="File is not shared publicly!")

    if sharedFile.check_expiration() is True:
        raise HTTPException(status_code=400, detail="File has expired!")
    
    file = sharedFile.file
    if not file:
        raise HTTPException(status_code=400, detail="File does not exist!")


    if file.size > app_config.max_preview_size:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds maximum preview size!",
        )

    if file.is_dir:
        raise HTTPException(status_code=400, detail="Cannot preview a directory!")

    path = file.path
    try:
        bucketName, filePath = getFilePath(path)
        mc.fget_object(bucketName, filePath, "/tmp/" + path)
        return "/tmp/" + path
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@files_router.post("/share_public", response_model=MessageResponse)
def share_public(
    path: Annotated[str, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user)],
    expiration: Annotated[int, Body(embed=True)] = 60,
):
    """
    Share the file specified by the path publicly.

    This function performs the following checks:

        - Check if the file exists.

        - Check if the user is the owner of the file.

    Then it creates a database entry for the share. While creating the share, it also checks if the user already has
    an existing share for the file and updates the permission if the new permission is higher than the existing
    permission.
    """
    file = File.objects(path=path).first()

    if not file:
        raise HTTPException(status_code=400, detail="File does not exist!")
    else:
        print(username)
        parent_usr = User.objects(username=username).first()
        if file.owner != parent_usr:
            raise HTTPException(
                status_code=400, detail="You do not have permission to share this file!"
            )

        expirationDate = datetime.now() + timedelta(minutes=expiration)

        uuid_token = str(uuid.uuid4())

        shared_file = SharedFile.objects(
            file=file, user=None, explicit=True, isPublic=True
        ).first()

        if shared_file is None:
            shared_file = SharedFile(
                file=file,
                permission=Permission.READ,
                explicit=True,
                isPublic=True,
                expiration=expirationDate,
                publicAccessToken=uuid_token,
                owner=parent_usr,
                user=parent_usr,
            )
            shared_file.save()

        else:
            shared_file.expiration = expirationDate
            shared_file.publicAccessToken = uuid_token
            shared_file.save()

    url = path + "?token=" + uuid_token
    print(url)
    return {
        "message": "File shared successfully!",
        "data": {
            "url": url,
        },
    }


@files_router.post("/share", response_model=MessageResponse)
def share(
    path: Annotated[str, Body(embed=True)],
    parent_username: Annotated[str, Depends(get_auth_user)],
    child_username: Annotated[str, Body(embed=True)],
    perm: Annotated[Permission, Body(embed=True)] = Permission.READ,
):
    """
    Share the file specified by the path with the user specified by the username.

    This function performs the following checks:
        - Check if the file exists.
        - Checks if the logged-in user is the owner of the file.
        - Checks if the logged-in user is not sharing with themselves.

    Then it creates a database entry for the share. While creating the share, it also checks if the user already has
    an existing share for the file and updates the permission if the new permission is higher than the existing
    permission.
    """
    file = File.objects(path=path).first()

    print(path)
    shared_list = []

    if not file:
        raise HTTPException(status_code=400, detail="File does not exist!")
    else:
        parent_usr = User.objects(username=parent_username).first()
        child_usr = User.objects(username=child_username).first()
        if parent_usr == child_usr:
            raise HTTPException(
                status_code=400, detail="You cannot share with yourself!"
            )
        if file.owner != parent_usr:
            raise HTTPException(
                status_code=400, detail="You do not have permission to share this file!"
            )

        shared_file = SharedFile.objects(
            file=file, user=child_usr, owner=parent_usr, explicit=True
        ).first()

        if shared_file is None:
            shared_file = SharedFile(
                file=file,
                user=child_usr,
                permission=perm,
                owner=parent_usr,
                explicit=True,
            )
            shared_file.save()

        else:
            if perm.value > shared_file.permission.value:
                shared_file.permission = perm
            shared_file.save()

        shared_list.append(shared_file)

    bucketName, filePath = getFilePath(path)
    for obj in mc.list_objects(bucketName, prefix=filePath + "/", recursive=True):
        if obj.object_name[-1] == "_":
            file_path = obj.object_name[:-2]
            file = File.objects(path=file_path).first()
        else:
            file = File.objects(path=obj.object_name).first()

        if file:
            shared_file = SharedFile.objects(
                file=file, user=child_usr, owner=parent_usr, explicit=False
            ).first()

            if shared_file:
                if perm.value > shared_file.permission.value:
                    shared_file.permission = perm
                    shared_file.save()
            else:
                shared_file = SharedFile(
                    file=file,
                    user=child_usr,
                    permission=perm,
                    explicit=False,
                    owner=parent_usr,
                )
                shared_file.save()

            shared_list.append(shared_file)

    return {"message": "File shared successfully!"}


@files_router.post("/list_shared_with", response_model=List[SharedFileModel])
def get_shared_with(
    username: Annotated[str, Depends(get_auth_user_optional)],
    path: Annotated[str, Body(embed=True)] = None,
    token: Annotated[str, Body(embed=True)] = None,
):
    """
    Lists the files shared with the user.

    If the path is specified, it lists the files shared with the user inside the directory specified by the path.
    Otherwise, it lists all the files explicitly shared with the user.
    """

    if token is not None:
        sharedFile = SharedFile.objects(publicAccessToken=token).first()
        if not sharedFile:
            raise HTTPException(status_code=400, detail="Invalid token!")
        if sharedFile.is_shared_public() is False:
            raise HTTPException(status_code=400, detail="File is not shared publicly!")

        if sharedFile.check_expiration() is True:
            raise HTTPException(status_code=400, detail="Link has expired!")
        file = sharedFile.file
        shared_list = []
        bucketName, filePath = getFilePath(file.path)
        if file.is_dir:
            for obj in mc.list_objects(
                bucketName, prefix=filePath + "/", recursive=False
            ):
                if obj.object_name[-1] == "_":
                    continue
                _shared_file = None
                if obj.is_dir:
                    _shared_file = SharedFile.objects(
                        file=File.objects(path=obj.object_name[:-1]).first(),
                        user=sharedFile.user,
                    ).first()
                else:
                    _shared_file = SharedFile.objects(
                        file=File.objects(path=obj.object_name).first(),
                        user=sharedFile.user,
                    ).first()
                shared_list.append(
                    {
                        "path": obj.object_name,
                        "is_dir": obj.is_dir,
                        "last_modified": obj.last_modified,
                        "size": obj.size,
                        "metadata": obj.metadata,
                        "permission": _shared_file.permission,
                        "explicit": _shared_file.explicit,
                        "shared_with": _shared_file.user.username,
                        "bucket": bucketName,
                    }
                )
        else:
            path_without_bucket = ""
            if file.path.startswith(bucketName):
                path_without_bucket = file.path[len(bucketName) + 1 :]
            shared_list.append(
                {
                    "path": path_without_bucket,
                    "is_dir": file.is_dir,
                    "last_modified": None,
                    "size": file.size,
                    "metadata": None,
                    "permission": sharedFile.permission,
                    "explicit": sharedFile.explicit,
                    "shared_with": sharedFile.user.username,
                    "bucket": bucketName,
                }
            )
        return shared_list
    else:   
        if username:
            user = User.objects(username=username).first()
        else:
            user = None
            return {"message": "You are not logged in!"}

        shared_list = []

        if path == username:
            for shared_file in SharedFile.objects(user=user, explicit=True):
                file = shared_file.file
                shared_list.append(
                    {
                        "path": file.path,
                        "is_dir": file.is_dir,
                        "last_modified": None,
                        "size": file.size,
                        "metadata": None,
                        "permission": shared_file.permission,
                        "explicit": shared_file.explicit,
                        "shared_with": shared_file.user.username,
                    }
                )
        else:
            file = File.objects(path=path).first()

            if file is None:
                raise HTTPException(status_code=400, detail="File does not exist!")
            else:
                shared_file = SharedFile.objects(user=user, file=file).first()
                bucketName, filePath = getFilePath(file.path)
                if shared_file:
                    if shared_file.file.is_dir:
                        for obj in mc.list_objects(
                            bucketName, prefix=filePath + "/", recursive=False
                        ):
                            if obj.object_name[-1] == "_":
                                continue
                            _shared_file = None
                            if obj.is_dir:
                                print(obj.object_name)
                                _shared_file = SharedFile.objects(
                                    user=user,
                                    file=File.objects(path=obj.object_name[:-1]).first(),
                                ).first()
                            else:
                                _shared_file = SharedFile.objects(
                                    user=user,
                                    file=File.objects(path=obj.object_name).first(),
                                ).first()
                            shared_list.append(
                                {
                                    "path": obj.object_name,
                                    "is_dir": obj.is_dir,
                                    "last_modified": obj.last_modified,
                                    "size": obj.size,
                                    "metadata": obj.metadata,
                                    "permission": _shared_file.permission,
                                    "explicit": _shared_file.explicit,
                                    "shared_with": _shared_file.user.username,
                                }
                            )
                    else:
                        shared_list.append(
                            {
                                "path": shared_file.file.path,
                                "is_dir": shared_file.file.is_dir,
                                "last_modified": None,
                                "size": shared_file.file.size,
                                "metadata": None,
                                "permission": shared_file.permission,
                                "explicit": shared_file.explicit,
                                "shared_with": shared_file.user.username,
                            }
                        )
        return shared_list


@files_router.post("/list_shared_by", response_model=List[SharedFileModel])
def get_shared_by(
    username: Annotated[str, Depends(get_auth_user_optional)],
):
    """
    Lists all the explicitly shared files/directories by the user.
    """
    if username is not None:
        user = User.objects(username=username).first()
        shared_list = []

        for shared_file in SharedFile.objects(owner=user, explicit=True):
            file = shared_file.file
            shared_list.append(
                {
                    "path": file.path,
                    "is_dir": file.is_dir,
                    "last_modified": None,
                    "size": file.size,
                    "metadata": None,
                    "permission": shared_file.permission,
                    "explicit": shared_file.explicit,
                    "shared_with": shared_file.user.username,
                }
            )

        return shared_list
    else:
        user = None
        return {"message": "You are not logged in!"}


@files_router.post("/unshare", response_model=MessageResponse)
def unshare(
    path: Annotated[str, Body(embed=True)],
    child_username: Annotated[str, Body(embed=True)],
    parent_username: Annotated[str, Depends(get_auth_user)],
):
    """
    Unshare the file specified by the path with the user specified by the username.

    This function performs the following checks:

        - Check if the file exists.

        - Check if the logged-in user is the owner of the file.

        - Check if the file being pointed by the path is explicitly shared with the user.

    Then it deletes the share database entry for the file and all the files inside the directory if the file is a
    directory.
    """
    file = File.objects(path=path).first()
    child_usr = User.objects(username=child_username).first()
    parent_usr = User.objects(username=parent_username).first()

    if file is None:
        raise HTTPException(status_code=400, detail="File does not exist!")
    else:
        if file.owner != parent_usr:
            raise HTTPException(
                status_code=400,
                detail="You do not have permission to unshare this file!",
            )

        if file.is_dir:
            explicit_share = SharedFile.objects(
                file=file, user=child_usr, owner=parent_usr, explicit=True
            ).first()

            if explicit_share is None:
                raise HTTPException(
                    status_code=400,
                    detail="File is not explicitly shared with this user!",
                )
            else:
                explicit_share.delete()
                for _file in File.objects(path__startswith=path):
                    shared_file = SharedFile.objects(
                        file=_file, user=child_usr, explicit=False, owner=_file.owner
                    ).first()
                    if shared_file is not None:
                        shared_file.delete()

                refresh_share_perms(parent_username)
                return {"message": "Files unshared successfully!"}
        else:
            shared_file = SharedFile.objects(
                file=file, user=child_usr, explicit=True
            ).first()
            if shared_file is None:
                raise HTTPException(
                    status_code=400,
                    detail="File is not explicitly shared with this user!",
                )
            else:
                shared_file.delete()
                refresh_share_perms(parent_username)
                return {"message": "File unshared successfully!"}


# not altered
@files_router.post("/copy", response_model=MessageResponse)
def copy(
    src_path: Annotated[str, Body(embed=True)],
    dest_path: Annotated[str, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user)],
):
    """
    Copies the file/folder specified by the src_path to the destination folder specified by the dest_path.

    This function performs the following checks:

        - Check if the source file/folder exists.

        - Check if the destination folder exists.

        - Check if the destination is a directory.

        - Check if the user has write permission for the destination folder.

        - Check if the user has read permission for the source file/folder.

    Then it copies the file/folder specified by the src_path to the destination folder specified by the dest_path on the
    minio server and creates a database entry for the file/folder in the mongo database. It also inherits the share
    permissions from the parent directory.

    """
    usr = User.objects(username=username).first()
    src_file = File.objects(path=src_path).first()
    dest_file = File.objects(path=dest_path).first()

    parent_path = os.path.dirname(src_path)

    print(src_path)
    if src_file is None:
        raise HTTPException(
            status_code=400, detail="Source file/folder does not exist!"
        )

    if src_file.can_read(usr) is False:
        raise HTTPException(
            status_code=400, detail="You do not have permission to access this file!"
        )

    if dest_file is None:
        raise HTTPException(
            status_code=400, detail="Destination folder does not exist!"
        )
    elif not dest_file.is_dir:
        raise HTTPException(status_code=400, detail="Destination is not a directory!")

    if dest_file.can_write(usr) is False:
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to write to the destination folder!",
        )

    quota_user = User.objects(username=dest_path.split("/")[0]).first()
    copy_size = src_file.get_size()
    if quota_user.storage_used + copy_size > quota_user.storage_quota:
        raise HTTPException(status_code=400, detail="User storage quota exceeded!")

    if File.objects(path=dest_path + src_path[len(parent_path) :]).first():
        raise HTTPException(
            status_code=400, detail="Destination file/folder already exists!"
        )

    if src_file.is_dir:

        extra = ""
        if File.objects(path=dest_path + extra + src_path[len(parent_path) :]).first():
            extra += "/_copy"

        dest_public = dest_file.public

        for obj in mc.list_objects(MINIO_BUCKET, prefix=src_path + "/", recursive=True):
            mc.copy_object(
                MINIO_BUCKET,
                dest_path + obj.object_name[len(parent_path) :],
                minio.commonconfig.CopySource(MINIO_BUCKET, obj.object_name),
            )

        for file in File.objects(path__startswith=src_path):
            File(
                path=dest_path + file.path[len(parent_path) :],
                size=file.size,
                owner=dest_file.owner,
                public=dest_public,
                is_dir=file.is_dir,
            ).save()
    else:
        mc.copy_object(
            MINIO_BUCKET,
            dest_path + src_path[len(parent_path) :],
            minio.commonconfig.CopySource(MINIO_BUCKET, src_path),
        )
        File(
            path=dest_path + src_file.path[len(parent_path) :],
            size=src_file.size,
            owner=dest_file.owner,
            public=src_file.public,
            is_dir=src_file.is_dir,
        ).save()

    refresh_share_perms(dest_file.owner.username)

    quota_user.storage_used += copy_size
    quota_user.save()

    return {"message": "File/folder copied successfully!"}

# not altered
@files_router.post("/move", response_model=MessageResponse)
def move(
    src_path: Annotated[str, Body(embed=True)],
    dest_path: Annotated[str, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user)],
):
    """
    Moves the file/folder specified by the src_path to the destination folder specified by the dest_path.

    This function performs the following checks:

        - Check if the source file/folder exists.

        - Check if the destination folder exists.

        - Check if the destination is a directory.

        - Check if the user has write permission for the destination folder.

        - Check if the user has write permission for the source file/folder.

    Then it moves the file/folder specified by the src_path to the destination folder specified by the dest_path on the
    minio server and updates the database entry for the file/folder in the mongo database. It also inherits the share
    permissions from the parent directory of the destination folder.
    """

    usr = User.objects(username=username).first()
    src_file = File.objects(path=src_path).first()
    dest_file = File.objects(path=dest_path).first()

    parent_path = os.path.dirname(src_path)

    if src_file is None:
        raise HTTPException(
            status_code=400, detail="Source file/folder does not exist!"
        )

    if src_file.can_write(usr) is False:
        raise HTTPException(
            status_code=400, detail="You do not have permission to move this file!"
        )

    if dest_file is None:
        raise HTTPException(
            status_code=400, detail="Destination folder does not exist!"
        )

    if dest_file.can_write(usr) is False:
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to write to the destination folder!",
        )

    if not dest_file.is_dir:
        raise HTTPException(status_code=400, detail="Destination is not a directory!")

    dest_public = dest_file.public

    if src_file.is_dir:
        for obj in mc.list_objects(MINIO_BUCKET, prefix=src_path + "/", recursive=True):
            mc.copy_object(
                MINIO_BUCKET,
                dest_path + obj.object_name[len(parent_path) :],
                minio.commonconfig.CopySource(MINIO_BUCKET, obj.object_name),
            )
            mc.remove_object(MINIO_BUCKET, obj.object_name)

        for file in File.objects(path__startswith=src_path):
            shares = SharedFile.objects(file=file)
            file.path = dest_path + file.path[len(parent_path) :]
            file.owner = dest_file.owner
            file.public = dest_public
            file.save()
            for _share in shares:
                _share.delete()

        refresh_share_perms(dest_file.owner.username)
        return {"message": "File/folder moved successfully!"}

    else:
        obj = mc.copy_object(
            MINIO_BUCKET,
            dest_path + src_path[len(parent_path) :],
            minio.commonconfig.CopySource(MINIO_BUCKET, src_path),
        )
        mc.remove_object(MINIO_BUCKET, src_path)

        to_move_file = File.objects(path=src_path).first()
        to_move_file.path = dest_path + to_move_file.path[len(parent_path) :]
        to_move_file.owner = dest_file.owner
        to_move_file.public = dest_public
        to_move_file.save()

        for _share in SharedFile.objects(file=to_move_file):
            _share.delete()

        refresh_share_perms(dest_file.owner.username)
        return {"message": "File/folder moved successfully!"}


@files_router.post("/rename", response_model=MessageResponse)
def rename(
    src_path: Annotated[str, Body(embed=True)],
    new_name: Annotated[str, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user)],
):
    """
    Renames the file/folder specified by the src_path to the new_name.
    The new folder will be in the same directory as the old one.
    """

    src_file = File.objects(path=src_path).first()

    if not src_file:
        raise HTTPException(status_code=400, detail="File does not exist!")

    if not src_file.can_write(username):
        raise HTTPException(
            status_code=400, detail="You do not have permission to rename this file!"
        )

    # check if the new name is valid, i.e. it does not contain any slashes, and it does not already exist
    if "/" in new_name:
        raise HTTPException(status_code=400, detail="Invalid name!")

    if File.objects(path=os.path.dirname(src_path) + "/" + new_name).first():
        raise HTTPException(
            status_code=400, detail="File already exists with that name!"
        )
    bucketName, filePath = getFilePath(src_path)
    if not src_file.is_dir:
        mc.copy_object(
            bucketName,
            os.path.dirname(filePath) + "/" + new_name,
            minio.commonconfig.CopySource(bucketName, filePath),
        )
        mc.remove_object(bucketName, filePath)

        src_file.path = bucketName+"/"+ os.path.dirname(filePath) + "/" + new_name
        src_file.save()

        return {"message": "File renamed successfully!"}
    else:
        bucketName, fileName = getFilePath(src_path)
        for obj in mc.list_objects(bucketName, prefix=filePath + "/", recursive=True):
            mc.copy_object(
                bucketName,
                os.path.dirname(fileName)
                + "/"
                + new_name
                + obj.object_name[len(fileName) :],
                minio.commonconfig.CopySource(bucketName, obj.object_name),
            )
            mc.remove_object(bucketName, obj.object_name)

        for file in File.objects(path__startswith=src_path):
            file.path = (
               bucketName+ "/"+os.path.dirname(filePath) + "/" + new_name + file.path[len(filePath) :]
            )
            file.save()

        return {"message": "Folder renamed successfully!"}


@files_router.get("/get_all_files/{search_path:path}", response_model=List[ObjectModel])
def get_all_files(
    search_path: str,
    username: Annotated[str, Depends(get_auth_user_optional)],
):
    """
    Lists all the files in the specified directory.
    """

    search_path_file = File.objects(path=search_path).first()

    if not search_path_file:
        raise HTTPException(status_code=400, detail="File does not exist!")

    if search_path_file.is_dir is False:
        raise HTTPException(
            status_code=400, detail="Path does not point to a directory!"
        )

    if username:
        user = User.objects(username=username).first()
    else:
        raise HTTPException(status_code=400, detail="You are not logged in!")

    if not search_path_file.can_read(user):
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to access this directory!",
        )

    obj_json = []
    bucketName, filePath = getFilePath(search_path)
    for obj in mc.list_objects(bucketName, filePath + "/", recursive=True):
        obj_json.append(
            {
                "path": obj.object_name,
                "is_dir": obj.is_dir,
                "last_modified": obj.last_modified,
                "size": obj.size,
                "metadata": obj.metadata,
            }
        )

    return obj_json


class TokenResponse(BaseModel):
    token: str


@files_router.get("/token/{path:path}", response_model=TokenResponse)
def download_file(
    path: str,
    username: Annotated[str, Depends(get_auth_user_optional)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(clean_expired_jobs)
    file = File.objects(path=path).first()
    if not file:
        raise HTTPException(status_code=400, detail="File does not exist!")

    user = User.objects(username=username).first()
    if not file.can_read(user):
        raise HTTPException(
            status_code=400, detail="You do not have permission to access this file!"
        )

    # generate a token for download
    token = secrets.token_urlsafe(32)
    if file.is_dir:
        files = File.objects(path__startswith=path + "/")
        background_tasks.add_task(create_job, token, files, username, path)
    else:
        background_tasks.add_task(create_job, token, [file], username, None)

    return {"token": token}

# do changes after this
@files_router.post("/tokenPublic", response_model=TokenResponse)
def download_file(
    path: Annotated[str, Body(embed=True)],
    token: Annotated[str, Body(embed=True)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(clean_expired_jobs)
    sharedFile = SharedFile.objects(publicAccessToken=token).first()

    if not sharedFile:
        raise HTTPException(status_code=400, detail="Invalid token!")
    
    if sharedFile.is_shared_public() is False:
        raise HTTPException(status_code=400, detail="File is not shared publicly!")

    if sharedFile.check_expiration() is True:
        raise HTTPException(status_code=400, detail="File has expired!")
    
    file = sharedFile.file
    if not file:
        raise HTTPException(status_code=400, detail="File does not exist!")
    
    # check if path is sam as or a child of the shared file
    if not file.path.startswith(path):
        raise HTTPException(status_code=400, detail="Invalid path!")

    username = sharedFile.user.username
    # generate a token for download
    token = secrets.token_urlsafe(32)
    if file.is_dir:
        files = File.objects(path__startswith=path + "/")
        background_tasks.add_task(create_job, token, files, username, path)
    else:
        background_tasks.add_task(create_job, token, [file], username, None)

    return {"token": token}


class StatusResponse(BaseModel):
    status: str
    progress: int


@files_router.get("/status/{token}", response_model=StatusResponse)
def token_status(token: str):
    job = Job.objects(token=token).first()
    if not job:
        raise HTTPException(status_code=400, detail="Job does not exist!")

    return {"status": job.status.value, "progress": job.progress}


@files_router.get("/download/{token}", response_class=FileResponse)
def download(token: str):
    job = Job.objects(token=token).first()
    if not job or job.expired:
        raise HTTPException(status_code=400, detail="Job does not exist!")

    if job.status != Status.DONE:
        raise HTTPException(status_code=400, detail="Job not done yet!")

    job.expired = True
    job.exp_time = datetime.now() + timedelta(
        minutes=job.size / (60 * app_config.min_bandwidth)
    )
    job.save()

    return job.download_path


@files_router.post("/mark_public", response_model=MessageResponse)
def mark_public(
    path: Annotated[str, Body(embed=True)],
    username: Annotated[str, Depends(get_auth_user)],
    perm: Annotated[Permission, Body(embed=True)] = Permission.READ,
):
    """
    Mark a file or directory as public.

    This function performs the following checks:

        - Check if the file/dir exists.

        - Check if the user has write permission for the file/dir.

    Then it marks the file/dir as public and updates the database entries for the file/dir and all the files/dirs inside
    the directory if the file/dir is a directory.
    """
    file = File.objects(path=path).first()
    if not file:
        raise HTTPException(status_code=400, detail="File/dir does not exist!")

    user = User.objects(username=username).first()
    if not file.can_write(user):
        raise HTTPException(
            status_code=400,
            detail="You do not have permission to make this file public!",
        )

    if file.is_dir:
        for _file in File.objects(path__startswith=path):
            _file.public = perm
            _file.save()
    else:
        file.public = perm
        file.save()

    return {"message": "File marked public successfully!"}


def refresh_share_perms(username: str):
    """
    Refresh the share permissions for a user.

    For all the explicitly shared files/directories by the user, it updates the share permissions for the that share and
    all the files/directories inside the directory if the file/directory is a directory.
    """

    user = User.objects(username=username).first()

    for explicit_share in SharedFile.objects(owner=user, explicit=True):
        for file in File.objects(path__startswith=explicit_share.file.path + "/"):
            print(file.path, explicit_share.user.username)
            existing_share = SharedFile.objects(
                user=explicit_share.user, file=file, explicit=False, owner=file.owner
            ).first()

            if existing_share == None:
                print(
                    "Creating share",
                    file.path,
                    explicit_share.user.username,
                    file.owner,
                )
                SharedFile(
                    file=file,
                    user=explicit_share.user,
                    permission=explicit_share.permission,
                    explicit=False,
                    owner=file.owner,
                ).save()

# function to fetch the buckets, the user has access to, based on their username
@files_router.get("/get_bucket_list/", response_model=MessageResponse)
def get_bucket_list(username: str):
    user = User.objects(username=username).first()
    access_buckets = AccessBuckets.objects(user=user)
    bucket_list = []
    for access_bucket in access_buckets:
        bucket_list.append(access_bucket.bucket)
    return {
        "message": "Bucket list fetched successfully!",
        "data": {
            "bucket_list": bucket_list,
        },
    }
