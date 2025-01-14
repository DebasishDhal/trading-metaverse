from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.utils.mongo_utils import mongo_client
from backend.app.utils.goods_utils import Good

import uuid, datetime, os

router = APIRouter(
    prefix="/goods",
    tags=["Goods"]
)

@router.post("/sync_goods")
async def sync_goods(admin_password: str):
    #Syncs goods from spawn points to goods collection. I added spawns and populated the goods manually for trial.
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can sync goods"})

    db = mongo_client["outposts"]
    collection_name = "spawn_points"

    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Spawn points Database not found"})

    spawn_collection = db[collection_name]
    spawn_points = list(spawn_collection.find({}))

    goods_collection = db["goods"]
    count = 0
    for spawn_point in spawn_points:
        good_list = spawn_point["goods_available"]
        for good in good_list:
            existing_quantity = 0
            #First check, if such good already exists at that output, if yes, add
            existing_good = goods_collection.find_one({"name": good["name"], "outpost_id": spawn_point["id"]})
            if existing_good:
                existing_quantity = existing_good["good_quantity"]
            good["outpost_id"] = spawn_point["id"]
            good["quantity"] = good["quantity"] + existing_quantity
            good["last_updated"] = datetime.datetime.now()

            if existing_good:
                goods_collection.update_one({"name": good["name"], "outpost_id": spawn_point["id"]}, {"$set": good})
                count += 1
            else:
                goods_collection.insert_one(good)
                count += 1
    return JSONResponse(status_code=200, content={"message": f"Goods synced successfully with {count} updates."})

@router.post("/add_goods")
async def add_good(good: Good, admin_password: str):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can add goods"})
    
    db = mongo_client["outposts"]
    collection_name = "goods"

    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)

    collection = db[collection_name]

    if good.id is None:
        # good.id = str(uuid.uuid4())
        good.id = str(good.good_name.replace(" ", "_").lower())
    
    good_data = good.model_dump()
    good_data["last_updated"] = datetime.datetime.now()
    
    collection.insert_one(good_data)
    return JSONResponse(status_code=200, content={"message": "Good added successfully", "good": str(good_data)})

@router.post("/update_goods")
async def update_good(good_id: str, good: dict, admin_password: str):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can update goods"})

    db = mongo_client["outposts"]
    collection_name = "goods"

    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Goods Database not found"})

    collection = db[collection_name]

    good_data = good
    good_data["last_updated"] = datetime.datetime.now()
    
    # Check if good exists
    existing_good = collection.find_one({"id": good_id})
    if not existing_good:
        return JSONResponse(status_code=404, content={"message": "Good not found"})

    collection.update_one({"id": good_id}, {"$set": good_data})
    return JSONResponse(status_code=200, content={"message": "Good updated successfully", "good": str(good_data)})


@router.get("/fetch/{outpost}")
async def fetch_goods(outpost: str):
    db = mongo_client["outposts"] #Bruh, I accidentally typed "outpostS, took me 5 min. to figure out"
    collection = db["goods"]
    
    #Print total number of docs in this collection
    # print(collection.count_documents({}))
    # print(collection.find_one({"outpost_id": outpost}))

    goods = list(collection.find({"outpost_id": outpost}))
    
    if not goods:
        return JSONResponse(status_code=404, content={"message":"No goods found for this outpost"})
    
    return JSONResponse(status_code=200, content={"outpost": outpost, "goods": str(goods)})


@router.post("/delete/{good_id}")
async def delete_good(good_id: str, admin_password: str):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can delete goods"})
    
    db = mongo_client["outposts"]
    collection = db["goods"]

    result = collection.delete_one({"id": good_id})
    if result.deleted_count == 0:
        return JSONResponse(status_code=404, detail="Good not found")
    
    return {"message": "Good deleted successfully"}
