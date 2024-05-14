#!/usr/bin/env python
import argparse

from config import MONGO_CONFIG

from models.orm import init_db, disconnect_db
from models.user import User, AccessBuckets
from models.common import Role


def create_admin():
    print(
        """
    You are now creating an admin user.
    Ensure that the user has already registered on the platform.
    """
    )
    username = input("Username: ")
    user = User.objects(username=username).first()
    if not user:
        print("User does not exist")
        return
    # user.admin = True
    user.role = Role.ADMIN
    user.save()
    print(f"User '{username}' is now an admin")

def create_bucket():
    print("Creating Bucket")
    user = User.objects(username="shreyashjain1007@gmail.com").first()
    print(user)
    buckets = AccessBuckets(
        username = user,
        bucket_name = "test-1"
    ).save()
    

actions = {
    "create-admin": create_admin,
}


def main():
    parser = argparse.ArgumentParser(
        description="This application is used to manage the data drive backend"
    )
    parser.add_argument("action", help="Action to be performed", choices=actions.keys())
    args = parser.parse_args()

    init_db(MONGO_CONFIG)
    actions[args.action]()
    disconnect_db()


if __name__ == "__main__":
    main()
