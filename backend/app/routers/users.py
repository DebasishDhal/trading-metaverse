from fastapi import APIRouter, UploadFile, File, Form

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
import json
import os
from dotenv import load_dotenv
import datetime, time
from zoneinfo import ZoneInfo

load_dotenv()

timezone = str(os.getenv("TIME_ZONE")).strip()

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Get all users
@router.get("/")
async def get_users():
    # print("confirmation get_users")
    return {"users": ["John Doe", "Jane Smith"]}

# Get a user by ID
@router.get("/find_user")
#Fetches a user by user_id or username. Admin password is required. add_user in auth.py
async def get_user(admin_password : str, user_id = '', username = ''):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code = 400, content = {"message": "Invalid admin password"})
    
    if not user_id and not username:
        return JSONResponse(status_code=400, content={"message": "User ID or username is required"})
    database_name = "users"
    collection_name = "metaverse_users"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Database not found"})
    
    collection = db[collection_name]

    #Find a user by either user_id or username, it's a union not intersection
    user = collection.find_one({"$or": [{"user_id": user_id}, {"username": username}]})

    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    
    return JSONResponse(status_code=200, content={"userId": user.get("user_id"), "username": user.get("username"), "created_at": user.get("created_at"), "updated_at": user.get("updated_at")})

@router.post("/delete_user")
async def delete_user(user_id: str):
    database_name = "users"
    collection_name = "metaverse_users"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Database not found"})
    
    collection = db[collection_name]

    user = collection.find_one({"username": user_id})

    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})

    collection.delete_one({"username": user_id})

    return JSONResponse(status_code=200, content={"message": "User deleted"})

@router.post("/add_avatar")
#Function adds avatar to database. Admin password is required
async def fetch_avatars(
    admin_password: str,
    avatar_name: str = Form(...),
    file: UploadFile = File(...)
):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code = 400, content = {"message": "Invalid admin password"})
    
    folder_path = "static/avatars"
    os.makedirs(folder_path, exist_ok=True)

    avatar_file_path = os.path.join(folder_path, file.filename)

    #Check if file already exists
    if os.path.exists(avatar_file_path):
        return JSONResponse(status_code=400, content={"message": "Avatar already exists"})
    
    with open(avatar_file_path, "wb") as f:
        f.write(await file.read())
    
    avatar_data = {
        "name" : avatar_name,
        "path" : avatar_file_path,
        "id" : generate_uuid(),
        "created_at" : datetime.datetime.now(),
    }

    database_name = "users"
    collection_name = "avatars"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
    
    collection = db[collection_name]

    collection.insert_one(avatar_data)

    return JSONResponse(status_code=200, content={"message": "Avatar added"})

@router.get("/fetch_avatar")
#Function returns information of a single avatar, based on the avatar_id
def fetch_avatar(avatar_id: str = ''):
    database_name = "users"
    collection_name = "avatars"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Database not found"})
    
    collection = db[collection_name]

    correct_avatar = collection.find_one({"id": avatar_id})

    if not correct_avatar:
        return JSONResponse(status_code=404, content={"message": "Avatar not found"})
    # print(correct_avatar)
    # print(correct_avatar["id"])
    return JSONResponse(status_code=200, content=json.dumps({k: v for k, v in correct_avatar.items() if k not in ["_id", "created_at"]}))

@router.get("/fetch_all_avatars")
async def fetch_all_avatars():
#Function return information of all avatars
    database_name = "users"
    collection_name = "avatars"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Database not found"})
    
    collection = db[collection_name]

    avatars = collection.find({})
    if not avatars:
        return JSONResponse(status_code=404, content={"message": "No avatars found"})
    
    return JSONResponse(status_code=200, content=json.dumps([{k:v for k,v in avatar.items() if k not in ["_id", "created_at"]} for avatar in avatars]))

@router.post("/delete_avatar")
# This function deletes the avatar from the codebase storage and from the database. Admin password is required
async def delete_avatar(admin_password:  str, avatar_id: str = ''):
    real_admin_password = os.getenv("ADMIN_PASSWORD")

    if admin_password != real_admin_password:
        return JSONResponse(status_code = 400, content = {"message": "Invalid admin password"})
    
    database_name = "users"
    collection_name = "avatars"

    if not avatar_id:
        return JSONResponse(status_code=400, content={"message": "Avatar ID is required"})
    
    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Database not found"})
    
    collection = db[collection_name]

    avatar_exists = collection.find_one({"id": avatar_id})
    if avatar_exists is None:
        return JSONResponse(status_code=404, content={"message": "Avatar not found in MongoDB"})
    
    avatar_path = avatar_exists["path"]
    if os.path.exists(avatar_path):
        os.remove(avatar_path)
        collection.delete_one({"id": avatar_id})
        return JSONResponse(status_code=200, content={"message": "Avatar deleted from codebase storage"})

    return JSONResponse(status_code=404, content={"message": "Avatar not found in codebase storage"})

@router.post("/update_avatar")
async def update_avatar(user_id: str, avatar_id: str):
    database_name = "users"
    collection_name = "metaverse_users"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Database not found"})
    
    collection = db[collection_name]

    user = collection.find_one({"user_id": user_id})

    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})

    collection.update_one({"user_id": user_id}, {"$set": {"avatar_id": avatar_id, "updated_at": datetime.datetime.now()}})

    return JSONResponse(status_code=200, content={"message": "Avatar updated"})

