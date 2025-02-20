from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.utils.outposts_utils import SpawnPoint, FetchSpawnPoint, DeleteSpawnPoint
from backend.app.utils.mongo_utils import mongo_client

import os, json, random, datetime

router = APIRouter(
    prefix="/outposts",
    tags=["Outposts"]
)

# List all outposts
@router.get("/")
async def list_outposts():
    return {"outposts": ["Siberian Frontier", "Indian Bazar", "Arab Souk"]}

@router.get("/route_coordinates")
async def route_coordinates():
    database_name = "transports"
    collection_name = "routes"

    db = mongo_client[database_name]
    collection = db[collection_name]

    routes = list(collection.find({}, {"_id": 0}))

    return JSONResponse(status_code=200, content=routes)

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
    print("Inside /outposts/fetch_spawn_points")
    db = mongo_client["outposts"]
    collection = db["spawn_points"]

    # Use MongoDB's aggregation framework to get selected fields
    spawn_points = list(collection.find(
        {},
        {'_id': 0, "goods_available": 0, "goods_demanded": 0, 'trade_routes': 0}
    ))

    # No need to use json.dumps(), FastAPI handles serialization automatically
    return JSONResponse(status_code=200, content=spawn_points)

@router.post("/choose_spawn_point")
async def choose_spawn_point(data: FetchSpawnPoint):
    print("Inside /outposts/choose_spawn_point")
    username = data.username
    spawn_id = data.spawn_id
    try:
        db_user = mongo_client["users"]
        db_outpost = mongo_client["outposts"]
        user_collection = db_user["metaverse_users"]
        spawn_collection = db_outpost["spawn_points"]

        # Check if spawn point exists
        existing_spawn_point = spawn_collection.find_one({"id": spawn_id})
        if not existing_spawn_point:
            return JSONResponse(status_code=404, content={"message": "Spawn point not found"})
        
        # Check if user exists
        existing_user = user_collection.find_one({"username": username})
        if not existing_user:
            return JSONResponse(status_code=404, content={"message": "User not found"})

        # Check if user has already chosen a spawn point
        if existing_user.get("chose_spawn_already"):
            return JSONResponse(status_code=400, content={"message": "User has already chosen a spawn point. Use transports to move to the chosen spawn point."})

        bonus_amount = existing_spawn_point.get("gold_bonus", 0)
        time = datetime.datetime.now()
        user_collection.update_one({"username": username}, {"$set": {"spawn_outpost_id": spawn_id, "current_outpost_id": spawn_id,"chose_spawn_already": True, "money": bonus_amount, "merchandise_weight": 0,"updated_at": time}})

        return JSONResponse(status_code=200, content={"message": "Spawn point chosen"})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/delete_spawn_point")
async def delete_spawn_point(request: DeleteSpawnPoint):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if request.admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can delete spawn points"})
    
    spawn_id = request.spawn_id

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