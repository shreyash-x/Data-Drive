from fastapi import (
                    Body,
                    Depends,
                    HTTPException,
                    APIRouter)
from models.bucket import Bucket,BucketAccessList, GroupAccessList,BucketType
from models.user import User
from typing import Annotated, List, Tuple
from models.file import File
from models.common import Role,Permission,Task
from tasks.bucket import create_bucket_helper, create_folder_helper
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
    
@bucket_router.post("/get_bucket_tasks",response_model=MessageResponse)
def get_bucket_tasks(bucket_name:Annotated[str,Body(embed=True)]):
    bucket = Bucket.objects(name=bucket_name).first()
    if bucket is None:
        raise HTTPException(status_code=400, detail="Bucket does not exist")
    try:
        data = File.objects(path__startswith=f"{bucket_name}/{bucket_name}",is_task_head=True)
        task_list = []
        for task in data:
            task_list.append({
                "task_name": task.path.split("/")[-1],
                "task_type": task.task_type.name
            })
        return {
            "message": "List of tasks in the bucket",
            "data": task_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@bucket_router.post("/get_group_space",response_model=MessageResponse)
def get_group_space(bucket_name:Annotated[str,Body(embed=True)]):
    print(" ==== DATA RECEIVED GROUP ==== ",bucket_name)
    bucket = Bucket.objects(name=bucket_name).first()
    
    if bucket is None:
        raise HTTPException(status_code=400, detail="Bucket does not exist")
    
    return {
        "message": "Group Space",
        "data": bucket.is_group_space()
    }
    
# changes role of user in bucket
@bucket_router.post("/change_bucket_permissions",response_model=MessageResponse)
def change_bucket_permissions(bucket_name:Annotated[str,Body(embed=True)],username:Annotated[str,Body(embed=True)],role:Annotated[str,Body(embed=True)]="USER",permission:Annotated[str,Body(embed=True)]="NONE"):
    print(" ==== DATA RECEIVED ==== ",bucket_name,username,role,permission)
    try:
        bucket = Bucket.objects(name=bucket_name).first()
        user = User.objects(username=username).first()
        bucket_permissions = BucketAccessList.objects(bucket = bucket,user = user).first()
        all_files = []
        print("Checkpoint 1 ")
        if bucket_permissions is None:
            bucket = Bucket.objects(name=bucket_name).first()
            user = User.objects(username=username).first()
            print("Checkpoint 2 ")
            if bucket is None or user is None:
                raise HTTPException(status_code=400, detail="Bucket or User does not exist")
            
            # Load all tasks in the bucket
            tasks = File.objects(path__startswith=f"{bucket_name}/{bucket_name}",is_task_head=True)
            for task in tasks:
                print("Found Task ",task.path," of type ",task.task_type)
                task_name = task.path.split("/")[-1]
                if task.has_personal_space():
                    print("creating personal space for ",username," in task ",task_name)
                    file = File(
                        path = f"{bucket_name}/{bucket_name}/{task_name}/{username}",
                        owner = user,
                        is_dir = True,
                        public = Permission.NONE,
                        parent_task_type = task.task_type
                    )
                    all_files.append(file)
                    print("Creating folder ",f"{bucket_name}/{task_name}/{username}")
                    # create a personal folder only when bucket has personal storage enabled
                    create_folder_helper(bucket_name, f"{bucket_name}/{task_name}/{username}")
                    print("DONE!")
                if task.task_type == Task.VIEWER:
                    print("HERE")
                    public_folder = File.objects(path=f"{bucket_name}/{bucket_name}/{task_name}/public").first()
                    if not public_folder:
                        public_folder = File(
                            path=f"{bucket_name}/{bucket_name}/{task_name}/public",
                            owner=user,
                            is_dir=True,
                            group_path=f"{bucket_name}/{bucket_name}/{task_name}/public",
                            parent_task_type=task.task_type,
                            public=Permission.NONE
                        )
                        public_folder.save()
                        create_folder_helper(bucket_name, f"{bucket_name}/{task_name}/public")
                    # check if user is present in the public folder
                    public_access_permission = GroupAccessList.objects(
                        bucket=bucket, group_name="public", user=user).first()
                    if public_access_permission is None:
                        public_access_permission = GroupAccessList(
                            bucket=bucket, group_name="public", user=user, permission=Permission.WRITE, path=f"{bucket_name}/{bucket_name}/{task_name}/public")
                        public_access_permission.save()
            _role = Role[role]        
            # if the user is admin or superadmin they, have the write permissions by default
            if role == "ADMIN":
                user.update(push__bucket_admin_list=bucket_name)
            
            if role =="ADMIN" or role=="SUPERADMIN":
                _permission = Permission.WRITE
            else: 
                _permission = Permission[permission]
            bucket_permissions = BucketAccessList(bucket=bucket,user=user,role=_role,permission=_permission)
            print("FOLLEE CREATE")
            try:
                user.update(role=_role)
                # if bucket.is_personal_space():
                #     file.save()
                for file in all_files:
                    file.save()
                bucket_permissions.save()
            except Exception as e:
                print(e)
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # update the bucket permissions
            _role = Role[role]
            
            if role == "ADMIN":
                user.update(push__bucket_admin_list=bucket_name)
                
            if role =="ADMIN" or role=="SUPERADMIN":
                _permission = Permission.WRITE
            else:
                _permission = Permission[permission]
            user.update(role=_role)
            bucket_permissions.update(role=_role,permission=_permission)
   
        return {
            "message": "Permissions updated"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
   
@bucket_router.post("/change_group_permissions", response_model=MessageResponse)
def change_group_permissions(
    bucket_name: Annotated[str, Body(embed=True)],
    task_name: Annotated[str, Body(embed=True)],
    usernames: Annotated[List[str], Body(embed=True)],
    group_name: Annotated[str, Body(embed=True)],
    permission: Annotated[str, Body(embed=True)] = "NONE"
):
    print(" ==== DATA RECEIVED ==== ", bucket_name, group_name, permission)
    response_messages = []
    bucket = Bucket.objects(name=bucket_name).first()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket does not exist")
    
    task = File.objects(path=f"{bucket_name}/{bucket_name}/{task_name}").first()
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")

    for username in usernames:
        try:
            user = User.objects(username=username).first()
            if not user:
                response_messages.append(f"User {username} does not exist")
                continue
        
            
            gname_user_clash = User.objects(username=group_name).first()
            if gname_user_clash:
                response_messages.append(f"Group name {group_name} clashes with a user name")
                return {"messages": response_messages}
            
            # Check if group name exists, if not create a folder in the root directory of the bucket
            group_folder = File.objects(path=f"{bucket_name}/{bucket_name}/{task_name}/{group_name}").first()
            if not group_folder:
                group_folder = File(
                    path=f"{bucket_name}/{bucket_name}/{task_name}/{group_name}",
                    owner=user,
                    is_dir=True,
                    group_path=f"{bucket_name}/{bucket_name}/{task_name}/{group_name}",
                    parent_task_type=task.task_type,
                    public=Permission.NONE
                )
                group_folder.save()  
                create_folder_helper(bucket_name, f"{bucket_name}/{task_name}/{group_name}")     
            
            def is_public_folder_present(task_type):
                return task_type == Task.VIEWER or task_type == Task.PAPER or task_type == Task.PROTOTYPE
            
            print("Public is :",is_public_folder_present(task.task_type))
            if is_public_folder_present(task.task_type):
                public_folder = File.objects(path=f"{bucket_name}/{bucket_name}/{task_name}/public").first()
                if not public_folder:
                    public_folder = File(
                        path=f"{bucket_name}/{bucket_name}/{task_name}/public",
                        owner=user,
                        is_dir=True,
                        group_path=f"{bucket_name}/{bucket_name}/{task_name}/public",
                        parent_task_type=task.task_type,
                        public=Permission.NONE
                    )
                    public_folder.save()
                    create_folder_helper(bucket_name, f"{bucket_name}/{task_name}/public")
                # check if user is present in the public folder
                public_access_permission = GroupAccessList.objects(
                    bucket=bucket, group_name="public", user=user).first()
                if public_access_permission is None:
                    public_access_permission = GroupAccessList(
                        bucket=bucket, group_name="public", user=user, permission=Permission.WRITE, path=f"{bucket_name}/{bucket_name}/{task_name}/public")
                    public_access_permission.save()
                    
            group_permissions = GroupAccessList.objects(
                bucket=bucket, group_name=group_name, user=user).first()

            if group_permissions is None:
                group_permissions = GroupAccessList(
                    bucket=bucket, group_name=group_name, user=user, permission=Permission.WRITE, path=f"{bucket_name}/{bucket_name}/{task_name}/{group_name}")
                group_permissions.save()
                response_messages.append(f"Permission {permission} set for user {username} in group {group_name}")
            else:
                group_permissions.update(permission=Permission[permission])
                response_messages.append(f"Permission updated to {permission} for user {username} in group {group_name}")

        except Exception as e:
            response_messages.append(f"Error for user {username}: {str(e)}")

    return {"message": "Permissions updated", "data": response_messages}

@bucket_router.get("/get_task_types",response_model=MessageResponse)
def get_task_types():
    # list the options of bucket type 
    return {
        "message": "List of task types",
        "data": [bucket_type.name for bucket_type in Task]    
    }
    
@bucket_router.post("/get_bucket_type",response_model=MessageResponse)
def get_bucket_type(bucket_name:Annotated[str,Body(embed=True)]):
    bucket = Bucket.objects(name=bucket_name).first()
    if bucket is None:
        raise HTTPException(status_code=400, detail="Bucket does not exist")
    return {
        "message": "Bucket Type",
        "data": bucket.bucket_type.name
    }
    
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
def create_bucket(bucket_name:Annotated[str,Body(embed=True)],bucket_type:Annotated[str,Body(embed=True)]="DEFAULT", tasks:Annotated[List[Tuple[str,str]],Body(embed=True)]=[]):
    bucket = Bucket.objects(name=bucket_name).first()
    if bucket is not None:
        raise HTTPException(status_code=400, detail="Bucket already exists")
    # create a new bucket in minio
    try:
        # creats a bucket in the minio object server
        create_bucket_helper(bucket_name)
        bucket = Bucket(name=bucket_name,bucket_type=BucketType[bucket_type])
        bucket.save()
        file = File(
            path = bucket_name + "/" + bucket_name,
            owner = None,
            is_dir = True,
            public = Permission.READ
        )
        file.save()
        superAdmin = User.objects(role=Role.SUPERADMIN).first()
        # Now creating the tasks
        for task in tasks:
            task_name, task_type = task
            
            # Check if task name is unique
            task_file = File.objects(path=bucket_name + "/" + bucket_name + "/" + task_name).first()
            if task_file:
                print("Task ",task_name," already exists in bucket ",bucket_name)
                continue
            
            task_file = File(
                path = bucket_name + "/" + bucket_name + "/" + task_name,
                owner = superAdmin,
                is_dir = True,
                public = Permission.READ,
                task_type = Task[task_type],
                parent_task_type = Task[task_type],
                is_task_head = True
            )
            # rohit45
            task_file.save()
            create_folder_helper(bucket_name, f"{bucket_name}/{task_name}")
            print("Created task ",task_name," of type ",task_type," in bucket ",bucket_name)
        
        
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