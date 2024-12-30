from fastapi import APIRouter

from backend.app.utils.users_utils import UserSignupSchema, UserLoginSchema, generate_uuid
from backend.app.utils.mongo_utils import mongo_client
from backend.app.utils.security_utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from fastapi.responses import JSONResponse

import os
from dotenv import load_dotenv
import datetime, time
from zoneinfo import ZoneInfo

load_dotenv()

timezone = str(os.getenv("TIME_ZONE")).strip()

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/signup")
async def create_user(user: UserSignupSchema): #username, password, admin = False
    # print("confirmation create_user")
    user_dict = user.model_dump()
    database_name = "users"
    collection_name = "metaverse_users"

    # add user to database
    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        print("Database creation successful")
        db.create_collection(collection_name)

    collection = db[collection_name]
    print("Collection creation successful")

    username = user_dict["username"]

    #check for duplicate usernames, later email signup will be there
    if collection.find_one({"username": username}):
        return JSONResponse(status_code=400, content={"message": "Username already exists"})

    user_id = generate_uuid()
    user_dict["user_id"] = user_id
    
    creation_time = datetime.datetime.now()
    user_dict["created_at"] = creation_time
    user_dict["updated_at"] = creation_time

    password_hash = hash_password(user_dict["password"])
    user_dict["password"] = password_hash

    access_token = create_access_token(data={"sub": user_dict["username"]})
    refresh_token = create_refresh_token(data={"sub": user_dict["username"]})

    user_dict["access_token"] = access_token
    user_dict["refresh_token"] = refresh_token

    collection.insert_one(user_dict)

    return JSONResponse(status_code=200, content={"message": f"User created successfully with ID {user_id}"})

@router.post("/login")
def user_login(data: UserLoginSchema):
    database_name = "users"
    collection_name = "metaverse_users"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Database not found"})
    
    users_collection = db[collection_name]

    user = users_collection.find_one({"username": data.username})

    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})

    if not verify_password(data.password, user["password"]):
        return JSONResponse(status_code=401, content={"message": "Invalid password"})

    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    update_time = datetime.datetime.now()
    users_collection.update_one({"username": user["username"]}, {"$set": {"access_token": access_token, "refresh_token": refresh_token, "updated_at": update_time}})

    return JSONResponse(status_code=200, content={"message": "Login successful", "access_token": access_token, "refresh_token": refresh_token})


@router.post("/refresh-token")
async def refresh_token(refresh_token: str):
    # Decode the refresh token
    payload = decode_token(refresh_token, secret_key="your_refresh_secret_key")
    if not payload:
        return JSONResponse(status_code=401, detail="Invalid or expired refresh token")

    # Create a new access token
    username = payload.get("sub")
    if not username:
        return JSONResponse(status_code=401, detail="Invalid refresh token")

    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}