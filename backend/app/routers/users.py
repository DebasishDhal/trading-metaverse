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
async def get_user(user_id = '', username = ''):
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
    
    return JSONResponse(status_code=200, content={"userId": user.get("user_id"), "username": user.get("username")})
