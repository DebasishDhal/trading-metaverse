from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.utils.mongo_utils import mongo_client
from backend.app.utils.goods_utils import Good

from typing import Optional

import uuid, datetime, os

router = APIRouter(
    prefix="/goods",
    tags=["Goods"]
)

@router.post("/sync_goods") #Tested
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
                existing_quantity = existing_good["quantity"]
            good["outpost_id"] = spawn_point["id"]
            good["quantity"] = good["quantity"] + existing_quantity
            good["last_updated"] = datetime.datetime.now()
            good["type"] = "good"

            if existing_good:
                goods_collection.update_one({"name": good["name"], "outpost_id": spawn_point["id"]}, {"$set": good})
                count += 1
            else:
                goods_collection.insert_one(good)
                count += 1
    return JSONResponse(status_code=200, content={"message": f"Goods synced successfully with {count} updates."})

@router.post("/add_goods") #Tested
async def add_goods(good: Good, admin_password: str):
    """
    Adds a new good to the specified outpost. If the good already exists at the outpost, 
    it updates the quantity of the existing good. This function requires admin privileges.
serv
    Parameters:
    - good: Good - The good to be added, which includes details such as name, price, quantity, unit, and outpost_id.
    - admin_password: str - The admin password to authorize the addition of the good.

    Returns:
    - JSONResponse: A response indicating the success or failure of the operation.

    Notes:
    - Special care has been taken regarding value updates in database. Focus on inbuilt pymongo methods like $inc, instead of traditional updates, to avoid data loss during concurrent updates.
    """

    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can add goods"})
    
    db = mongo_client["outposts"]
    db = mongo_client["outposts"]
    goods_collection = db["goods"]
    spawn_collection = db["spawn_points"]

    if "type_1_name_1_outpost_id_1" not in goods_collection.index_information():
        goods_collection.create_index([("type", 1), ("name", 1), ("outpost_id", 1)], background=True, name="type_1_name_1_outpost_id_1")
    if "id_1" not in spawn_collection.index_information():
        spawn_collection.create_index([("id", 1)], background=True, name="id_1")

    good_data = good.model_dump()
    good_data["last_updated"] = datetime.datetime.now()
    good_data["type"] = "good"

    spawn_point = spawn_collection.find_one({"id": good_data["outpost_id"]})

    if not spawn_point:
        return JSONResponse(status_code=404, content={"message": "Outpost not found"})
        
    goods_available = spawn_point.get("goods_available", [])

    for item in goods_available:
        if item["name"] == good_data["name"]:
            item["quantity"] += good_data["quantity"]
            break
    else:
        goods_available.append({
        "name": good_data["name"],
        "price": good_data["price"], 
        "quantity": good_data["quantity"],
        "unit": good_data["unit"]
        })

    spawn_collection.update_one(
        {"id": good_data["outpost_id"]}, 
        {"$set": {"goods_available": goods_available}}
    )

    # # Use an atomic update operation with arrayFilters
    # spawn_collection.update_one(
    #     {"id": good_data["outpost_id"], "goods_available.name": good_data["name"]},
    #     {
    #         "$inc": {"goods_available.$.quantity": good_data["quantity"]},
    #         "$set": {"goods_available.$.last_updated": datetime.datetime.now()}
    #     }
    # )

    # # If the good was not found and updated, add it to the array, as it's a new good
    # if spawn_collection.modified_count == 0:
    #     spawn_collection.update_one(
    #         {"id": good_data["outpost_id"]},
    #         {
    #             "$push": {
    #                 "goods_available": {
    #                     "name": good_data["name"],
    #                     "price": good_data["price"],
    #                     "quantity": good_data["quantity"],
    #                     "unit": good_data["unit"],
    #                     "last_updated": datetime.datetime.now()
    #                 }
    #             }
    #         }
    #     )

    result = goods_collection.update_one(
        {"type": "good", "name": good_data["name"], "outpost_id": good_data["outpost_id"]},
        {"$inc": {"quantity": good_data["quantity"]}, "$set": {"last_updated": good_data["last_updated"]}},
        upsert= True
    )

    if result.upserted_id:
        message = f"Good added {good_data['name']} successfully"
    else:
        message = f"Good quantity added to existing good {good_data['name']} successfully"

    return JSONResponse(status_code=200, content={"message": message, "good": str(good_data)})

    # existing_good = goods_collection.find_one({
    #                                             "type": "good", 
    #                                             "name": good["name"], 
    #                                             "outpost_id": good["outpost_id"]
    #                                            })

    # if existing_good:
    #     # good_data["quantity"] = existing_good["quantity"] + good_data["quantity"]
    #     # goods_collection.update_one({"type": "good", "name": good["name"], "outpost_id": good["outpost_id"]}, 
    #     #                             {"$set": good_data})
    #     goods_collection.update_one({"type": "good", "name": good["name"], "outpost_id": good["outpost_id"]}, 
    #                                 {"$inc": {"quantity": good["quantity"]}, "$set": {"last_updated": datetime.datetime.now()}}
    #                                 ) #$inc will increase the quantity by good["quantity"] amount and avoid concurrency errors
    #     return JSONResponse(status_code=200, content={"message": f"Good quantity added to existing good {good['name']} successfully", "good": str(good_data)})

    # else:
    #     goods_collection.insert_one(good_data)
    #     return JSONResponse(status_code=200, content={"message": f"Good added {good['name']} successfully", "good": str(good_data)})

## TODO - Update the update_goods function according to the new schema
@router.post("/update_goods")
async def update_good(good: dict, admin_password: str):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can update goods"})

    if len(good.items()) <= 1:
        return JSONResponse(status_code=400, content={"message": "Good data not provided"})
    
    db = mongo_client["outposts"]
    collection_name = "goods"

    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Goods Database not found"})

    goods_collection = db[collection_name]

    good_data = good
    time = datetime.datetime.now()
    good_data["last_updated"] = time
    
    # Check if good exists
    existing_good = goods_collection.find_one({"name": good_data["name"]})
    if not existing_good:
        return JSONResponse(status_code=404, content={"message": "Good not found"})

    #Update it in spawn points as well
    spawn_collection = db["spawn_points"]

    outpost_document = spawn_collection.find_one({"id": good_data["outpost_id"]})
    if not outpost_document:
        return JSONResponse(status_code=404, content={"message": "Outpost not found"})

    goods_available = outpost_document.get("goods_available", [])

    for item in goods_available:
        if item["name"] == good_data["name"]:
            old_quantity = item["quantity"]
            old_unit = item["unit"]
            old_price = item["price"]
            item["quantity"] = good_data.get("quantity", old_quantity)
            item["unit"] = good_data.get("unit", old_unit)
            item["price"] = good_data.get("price", old_price)
            break

    spawn_result = spawn_collection.update_one({"id": good_data["outpost_id"]}, {"$set": {"goods_available": goods_available}})

    goods_result = goods_collection.update_one({"name": good_data["name"]}, {"$set": good_data})

    if goods_result.modified_count == 0:
        return JSONResponse(status_code=400, content={"message": "Good update failed"})
    
    if spawn_result.modified_count == 0:
        return JSONResponse(status_code=400, content={"message": "Good update failed"})

    return JSONResponse(status_code=200, content={"message": "Good updated successfully", "good": str(good_data)})


@router.get("/fetch/{outpost}") #Tested
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


@router.post("/delete/{good_name}") #Tested
async def delete_good(good_name: str, admin_password: str, outpost_id : Optional[str] = None):
    real_admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != real_admin_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can delete goods"})
    
    db = mongo_client["outposts"]
    goods_collection = db["goods"]
    spawn_collection = db["spawn_points"]

    if not outpost_id:
        goods_result = goods_collection.delete_many({"name": good_name})
        spawn_result = spawn_collection.update_many(
            {"goods_available.name": good_name},  # Match documents containing the good
            {"$pull": {"goods_available": {"name": good_name}}}  # Remove the matching good
        )


    else:
        goods_result = goods_collection.delete_one({"name": good_name, "outpost_id": outpost_id})
        # If outpost_id is provided, update only a single relevant document
        spawn_result = spawn_collection.update_one(
            {"id": outpost_id, "goods_available.name": good_name},  # Match the specific document
            {"$pull": {"goods_available": {"name": good_name}}}  # Remove the matching good
        )
                
    if goods_result.deleted_count == 0 or spawn_result.modified_count == 0:
        return JSONResponse(status_code=404, detail="Good not found")
    
    return {"message": "Good deleted successfully"}
