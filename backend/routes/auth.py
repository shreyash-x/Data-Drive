from datetime import datetime, timedelta
from typing import Annotated, List
import requests

from fastapi import APIRouter, Depends, HTTPException, Body, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from mongoengine.queryset.visitor import Q
from config import AUTH_URL, SECRET_KEY, ALGORITHM,MINIO_BUCKET, ACCESS_TOKEN_EXPIRE_MINUTES, app_config
from dependencies import get_auth_user, MessageResponse, oauth2_scheme
from models.common import Permission, Role, Task
from models.user import User, InvalidToken,AccessBuckets
from models.bucket import BucketAccessList, GroupAccessList
from models.file import File
from tasks.bucket import create_folder_helper, create_bucket_helper

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

class Token(BaseModel):
    access_token: str
    token_type: str

# creates an admin fro existing user 
@auth_router.post("/create_admin", response_model=MessageResponse)
def create_admin(username: Annotated[str, Body(...)]):
    """
    Creates an admin for an existing user.

    - **username**: Username of the user.
    """
    print("Creating admin")
    print(username)
    user = User.objects(username=username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # user.admin = True
    user.role = Role.ADMIN
    user.save()
    return {"message": f"{username} is now an admin"}



@auth_router.post("/login", response_model=Token)
def login(data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response):
    """
    Login a user.

    - **username**: Username of the user.
    - **password**: Password of the user.

    Checks if the user exists and the password is correct and returns an access token.
    """
    # Get user data from request
    username = data.username
    password = data.password

    # send request to auth server
    if AUTH_URL:
        r = requests.post(
            f"{AUTH_URL}/login",
            json={"email": username, "password": password},
        )

        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        data = r.json().get("data", {})
        username = data.get("user").get("user_email")
        if not username:
            raise HTTPException(status_code=400, detail="Invalid credentials")
    else:
        if not username or not password:
            raise HTTPException(status_code=400, detail="Invalid credentials")

    # Check if user exists in database
    user = User.objects(username=username).first()
    superAdmin = User.objects(role=Role.SUPERADMIN).first()
    if not user:
        user = User(
            username=username,
            email=username,
            password=password,
            storage_quota=app_config.default_user_quota,
            permission=Permission(app_config.default_user_permission),
        ).save()
        if not superAdmin:
            superAdmin = user
        
        # Check if default folders are created
        bucket_folder = File.objects(path="data-drive/data-drive").first()
        if not bucket_folder:
            File(path='data-drive/data-drive', size=0, owner=superAdmin, is_dir=True, public=Permission.READ).save()
            create_bucket_helper("data-drive")
       
        File(path='data-drive/data-drive/'+username, size=0, owner=user, is_dir=True, public=Permission.NONE,task_type = Task.DEFAULT ,parent_task_type=Task.DEFAULT).save()
        # always create personal storage space in data-drive folder.
        create_folder_helper("data-drive", f"data-drive/{username}")
        
        # for i in range(1,3):
        #     AccessBuckets(username=user, bucket_name=f"test-{i}").save()
        #     File(path=f'test-{i}/test-{i}/{username}', size=0, owner=user, is_dir=True, public=Permission.READ).save()
        #     create_folder_helper(f"test-{i}", f"test-{i}/{username}")
        print("User created successfully")
        

    # Create access token
    print("Setting admin role as: ", user.role == Role.ADMIN or user.role == Role.SUPERADMIN)
    access_token = jwt.encode(
        {
            "username": str(user.username),
            "admin": user.role == Role.ADMIN or user.role == Role.SUPERADMIN,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/logout", response_model=MessageResponse)
def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Handles logout of a user.

    - **token**: Access token of the user.

    Adds the access token to the invalid token database. So that the access token cannot be used again until it expires.
    """
    if token is None:
        raise HTTPException(status_code=400, detail="Auth token is missing")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        exp = datetime.fromtimestamp(exp)
        username = payload.get("username")
        if username is None or exp is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        if InvalidToken.objects(token=token).first() is None:
            InvalidToken(token=token, exp=exp).save()

        return {"message": "Logged out successfully!"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")


class UserSession(BaseModel):
    username: str | None
    super_admin: bool | None
    bucket_name:str | None
    bucket_list: List[str] | None
    permission: int | None
    storage_quota: int | None
    storage_used: int | None
    roles: List[str] | None
    access_groups: List[str] | None


@auth_router.get("/user", response_model=UserSession)
def user(username: Annotated[UserSession, Depends(get_auth_user)]):
    """
    Returns the username, privilege level, storage quota and storage used of the user.
    """
    user = User.objects(username=username).first()
    buckets = BucketAccessList.objects(user = user)
    access_groups = GroupAccessList.objects(user = user)
    print("Resultant Query: ",buckets)
    
    bucket_list1 = [bucket.bucket.name for bucket in buckets] if buckets else []
    access_groups_list = [group.group_name for group in access_groups] if access_groups else []
    # bucket_list = []
    # for bucket in buckets:
    #     bucket_list.append({
    #         "bucket_name": bucket.bucket.name,
    #         "role": bucket.role.name,
    #         "permission": bucket.permission.name
    #     })
    return {
        "username": username,
        "bucket_name":MINIO_BUCKET,
        "bucket_list": bucket_list1,
        "super_admin": user.role == Role.SUPERADMIN,
        "permission": user.permission.value,
        "storage_quota": user.storage_quota,
        "storage_used": user.storage_used,
        "roles":user.bucket_admin_list,
        "access_groups": access_groups_list
    }


class UserOut(BaseModel):
    username: str
    email: EmailStr


@auth_router.get("/users", response_model=List[UserOut])
def get_all_users():
    """
    Get a list of all users in the database.
    """
    users = User.objects()
    return [{"username": user.username, "email": user.email} for user in users]
