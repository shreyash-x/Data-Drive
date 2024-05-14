from typing import Annotated, List
from pydantic import BaseModel
from dynaconf.loaders.toml_loader import write
from fastapi import APIRouter, Depends, HTTPException, Body

from config import app_config
from dependencies import get_admin, MessageResponse
from models.user import User
from mongoengine.queryset.visitor import Q

from models.bucket import BucketAccessList,Bucket, GroupAccessList
admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


class Stats(BaseModel):
    username: str
    bucket_name: str
    role: str
    email: str
    permission: int
    storage_quota: int
    storage_used: int
    access_groups: List[str]
    access_groups_permissions: List[int]


@admin_router.post("/users", response_model=List[Stats])
def stats(bucket_name:Annotated[str,Body(embed=True)]):
    print("~~~~~~~~~~ QUERY RECEIVED",bucket_name)
    bucket = Bucket.objects(name=bucket_name).first()
    users = []
    bucket_list = BucketAccessList.objects(bucket=bucket)
    print("~~~~~~~~~~ BUCKET LIST",bucket_list)
    for data in bucket_list:
        print("~~~~~~~~~~ DATA",data)
    roleMap = {
        0: "USER",
        1: "ADMIN",
        2: "SUPERADMIN"
    }
    for data in bucket_list:
        access_groups = GroupAccessList.objects(bucket=bucket, user=data.user)
        users.append(
            Stats(
                username=data.user.username,
                bucket_name=bucket_name,
                email=data.user.email,
                role=roleMap[data.role.value],
                permission=data.permission.value,
                storage_quota=data.storage_quota,
                storage_used=data.storage_used,
                access_groups=[group.group_name for group in access_groups],
                access_groups_permissions=[group.permission.value for group in access_groups]
            )
        )
    return users


class UpdateUserData(BaseModel):
    username: str
    permission: int
    storage_quota: int


@admin_router.post("/update_user", response_model=MessageResponse)
def update_user(
    admin: Annotated[bool, Depends(get_admin)],
    data: Annotated[UpdateUserData, Body(embed=True)],
):
    user = User.objects(username=data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User does not exist")
    user.permission = data.permission
    user.storage_quota = data.storage_quota
    user.save()
    return {"message": "User updated successfully!"}


class Config(BaseModel):
    max_preview_size: int | None
    min_bandwidth: int | None
    default_user_quota: int | None
    default_user_permission: int | None
    allowed_file_extensions: List[str] | None


@admin_router.get("/config", response_model=Config)
def get_config(admin: Annotated[bool, Depends(get_admin)]):
    print(app_config.max_preview_size)
    return Config(
        max_preview_size=app_config.max_preview_size,
        min_bandwidth=app_config.min_bandwidth,
        default_user_quota=app_config.default_user_quota,
        default_user_permission=app_config.default_user_permission,
        allowed_file_extensions=app_config.allowed_file_extensions,
    )


@admin_router.post("/update_config", response_model=MessageResponse)
def update_config(
    admin: Annotated[bool, Depends(get_admin)],
    data: Annotated[Config, Body(embed=True)],
):
    app_config.max_preview_size = data.max_preview_size
    app_config.min_bandwidth = data.min_bandwidth
    app_config.default_user_quota = data.default_user_quota
    app_config.default_user_permission = data.default_user_permission
    app_config.allowed_file_extensions = data.allowed_file_extensions

    write(
        "settings.toml",
        {
            "drive": {
                "max-preview-size": app_config.max_preview_size,
                "min-bandwidth": app_config.min_bandwidth,
                "default-user-quota": app_config.default_user_quota,
                "default-user-permission": app_config.default_user_permission,
                "allowed-file-extensions": app_config.allowed_file_extensions,
            }
        },
        merge=False,
    )

    return {"message": "Config updated successfully!"}
