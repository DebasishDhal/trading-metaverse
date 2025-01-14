from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.utils.users_utils import UserSignupSchema, SpawnPoint
from backend.app.utils.mongo_utils import mongo_client

import os, json, random

router = APIRouter(
    prefix="/outposts",
    tags=["Outposts"]
)

# List all outposts
@router.get("/")
async def list_outposts():
    return {"outposts": ["Siberian Frontier", "Indian Bazar", "Arab Souk"]}


# Get details of a specific outpost
@router.get("/{outpost_id}")
async def get_outpost(outpost_id: int):
    return {"outpost_id": outpost_id, "name": "Sample Outpost", "language": "Russian"}


@router.post("/add_spawn_point")
# async def add_spawn_point(spawn_point: dict, admin_password: str):
async def add_spawn_point(spawn_point: SpawnPoint, admin_password: str):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can add spawn points"})
    
    db = mongo_client["outposts"]
    collection = db["spawn_points"]

    spawn_point = spawn_point.model_dump()
    # Check if spawn point already exists
    existing_spawn_point = collection.find_one({"id": spawn_point["id"]})
    if existing_spawn_point:
        return JSONResponse(status_code=400, content={"message": "Spawn point already exists, update it using /update_spawn_point"})
    
    collection.insert_one(spawn_point)
    return JSONResponse(status_code=200, content={"message": "Spawn point added"})

@router.post("/update_spawn_point")
async def update_spawn_point(spawn_id:str, spawn_point:dict, admin_password: str):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can update spawn points"})
    
    db = mongo_client["outposts"]
    collection = db["spawn_points"]

    # Check if spawn point exists
    existing_spawn_point = collection.find_one({"id": spawn_id})
    if not existing_spawn_point:
        return JSONResponse(status_code=404, content={"message": "Spawn point not found"})
    
    collection.update_one({"id": spawn_id}, {"$set": spawn_point})
    return JSONResponse(status_code=200, content={"message": "Spawn point updated"})

@router.post("/fetch_spawn_points")
async def fetch_spawn_points():
    db = mongo_client["outposts"]
    collection = db["spawn_points"]

    spawn_points = sorted(list(collection.find({})), key=lambda x: x["id"])
    spawn_points = [{k:v for k,v in outpost.items() if k not in ["_id"]} for outpost in spawn_points]

    return JSONResponse(status_code=200, content=json.dumps(spawn_points))

@router.post("/choose_spawn_point")
async def choose_spawn_point(user_id: str, spawn_id: str):
    db_user = mongo_client["users"]
    db_outpost = mongo_client["outposts"]
    user_collection = db_user["metaverse_users"]
    spawn_collection = db_outpost["spawn_points"]

    # Check if spawn point exists
    existing_spawn_point = spawn_collection.find_one({"id": spawn_id})
    if not existing_spawn_point:
        return JSONResponse(status_code=404, content={"message": "Spawn point not found"})
    
    # Check if user exists
    existing_user = user_collection.find_one({"username": user_id})
    if not existing_user:
        return JSONResponse(status_code=404, content={"message": "User not found"})

    # Check if user has already chosen a spawn point
    if existing_user.get("chose_spawn_already"):
        return JSONResponse(status_code=400, content={"message": "User has already chosen a spawn point. Use transports to move to the chosen spawn point."})

    user_collection.update_one({"username": user_id}, {"$set": {"spawn_id": spawn_id, "current_outpost_id": spawn_id,"chose_spawn_already": True}})

    return JSONResponse(status_code=200, content={"message": "Spawn point chosen"})

@router.post("/delete_spawn_point")
async def delete_spawn_point(spawn_id: str, admin_password: str):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can delete spawn points"})
    
    db_user = mongo_client["users"]
    db_outpost = mongo_client["outposts"]
    user_collection = db_user["metaverse_users"]
    spawn_collection = db_outpost["spawn_points"]

    # Check if spawn point exists
    unique_spawn_ids = spawn_collection.distinct("id")

    if not unique_spawn_ids:
        return JSONResponse(status_code=404, content={"message": "No spawn points found"})
    if spawn_id not in unique_spawn_ids:
        return JSONResponse(status_code=404, content={"message": f"Spawn point with ID {spawn_id} not found"})
    
    unique_spawn_ids.remove(spawn_id)

    if not unique_spawn_ids:
        return JSONResponse(status_code=400, content={"message": f"Cannot delete the last spawn point with ID {spawn_id}"})

    user_collection.update_many(
        {"spawn_id": spawn_id},
        {"$set": {"spawn_id": random.choice(unique_spawn_ids), "chose_spawn_already": False}}
    )    

    spawn_collection.delete_one({"id": spawn_id})
    return JSONResponse(status_code=200, content={"message": "Spawn point deleted"})