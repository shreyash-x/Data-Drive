from fastapi import (
                    Body,
                    Depends,
                    HTTPException,
                    APIRouter)
from models.bucket import Bucket,BucketAccessList
from models.user import User
from typing import Annotated, List
from models.file import File
from models.common import Role,Permission
from tasks.bucket import create_bucket_helper
bucket_router = APIRouter(
    prefix="/buckets",
    tags=["bucket"],
    responses={404: {"description": "Not found"}},
)

from dependencies import MessageResponse

@bucket_router.get("/list_buckets",response_model=MessageResponse)
def list_buckets():
    data = Bucket.objects()
    bucket_list = [bucket.name for bucket in data]
    return {
        "message": "List of buckets",
        "data": bucket_list
    }
    
# changes role of user in bucket
@bucket_router.post("/change_bucket_permissions",response_model=MessageResponse)
def change_bucket_permissions(bucket_name:Annotated[str,Body(embed=True)],username:Annotated[str,Body(embed=True)],role:Annotated[str,Body(embed=True)]="USER",permission:Annotated[str,Body(embed=True)]="NONE"):
    print(" ==== DATA RECEIVED ==== ",bucket_name,username,role,permission)
    try:
        bucket = Bucket.objects(name=bucket_name).first()
        user = User.objects(username=username).first()
        bucket_permissions = BucketAccessList.objects(bucket = bucket,user = user).first()
        print("Checkpoint 1 ")
        if bucket_permissions is None:
            bucket = Bucket.objects(name=bucket_name).first()
            user = User.objects(username=username).first()
            if bucket is None or user is None:
                raise HTTPException(status_code=400, detail="Bucket or User does not exist")
            file = File(
                path = bucket_name + "/"+username,
                owner = user,
                is_dir = True,
                public = Permission.NONE
            )
            _role = Role[role]        
            # if the user is admin or superadmin they, have the write permissions by default
            if role =="ADMIN" or role=="SUPERADMIN":
                _permission = Permission.WRITE
            else: 
                _permission = Permission[permission] 
            bucket_permissions = BucketAccessList(bucket=bucket,user=user,role=_role,permission=_permission)
            print("FOLLEE CREATE")
            try:
                file.save()
                bucket_permissions.save()
            except Exception as e:
                print(e)
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # update the bucket permissions
            _role = Role[role]
            if role =="ADMIN" or role=="SUPERADMIN":
                _permission = Permission.WRITE
            else:
                _permission = Permission[permission]
            bucket_permissions.update(role=_role,permission=_permission)
        return {
            "message": "Permissions updated"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@bucket_router.get("/get_admin_buckets",response_model=MessageResponse)
def get_buckets_with_admin_permissions():
    data = BucketAccessList.objects(role=Role.ADMIN)
    bucket_list = []
    for bucket in data:
        bucket_list.append({
            "bucket_name": bucket.bucket.name,
            "admin": bucket.user.username
        })
    return {
        "message": "List of buckets with admin permissions",
        "data": bucket_list
    }
    
@bucket_router.post("/create_bucket")
def create_bucket(bucket_name:Annotated[str,Body(embed=True)]):
    bucket = Bucket.objects(name=bucket_name).first()
    if bucket is not None:
        raise HTTPException(status_code=400, detail="Bucket already exists")
    # create a new bucket in minio
    try:
        create_bucket_helper(bucket_name)
        bucket = Bucket(name=bucket_name)
        bucket.save()
        return {
            "message": "Bucket created"
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
 
@bucket_router.post("/get_bucket_users")
def get_bucket_users(bucket_name:Annotated[str,Body(embed=True)]):
    bucket = Bucket.objects(name=bucket_name).first()
    if bucket is None:
        raise HTTPException(status_code=400, detail="Bucket does not exist")
    try:
        data = BucketAccessList.objects(bucket=bucket)
        user_list = []
        for user in data:
            user_list.append({
                "username": user.user.username,
                "role": user.role.name,
                "permission": user.permission.name
            })
        return {
            "message": "List of users in the bucket",
            "data": user_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))   

@bucket_router.post("/get_user_roles")
def get_user_roles(username:Annotated[str,Body(embed=True)]):
    print(" ==== DATA RECEIVED  IN USER ROLES ==== ",username)
    user = User.objects(username=username).first()
    if user is None:
        raise HTTPException(status_code=400, detail="User does not exist")
    try:
        data = BucketAccessList.objects(user=user)
        bucket_list = []
        for bucket in data:
            bucket_list.append({
                "bucket_name": bucket.bucket.name,
                "role": bucket.role.name,
                "permission": bucket.permission.name
            })
        return {
            "message": "List of buckets for user",
            "data": bucket_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))