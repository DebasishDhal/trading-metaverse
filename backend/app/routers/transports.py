from fastapi import APIRouter, Header
from backend.app.utils.mongo_utils import mongo_client
from backend.app.utils.transports_utils import weight_unit_conversion_table, direct_distance_calculator, Transport
from fastapi.responses import JSONResponse

import os

router = APIRouter(
    prefix="/transports",
    tags=["Transports"]
)

@router.post("/add_transport_method") #Admin only
async def add_edit_transport_method(transport: Transport, admin_password: str = Header(None)): #Last tested, 13/02/2025
    actual_password = os.getenv("ADMIN_PASSWORD")

    if admin_password != actual_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can add/edit transport methods. Go away."})
    
    database_name = "transports"
    collection_name = "transport_methods"

    transport_type = transport.name
    is_it_an_edit = transport.edit

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)


    collection = db[collection_name]
    exists = collection.find_one({"name": transport_type})

    if is_it_an_edit:
        if not exists:
            return JSONResponse(status_code=400, content={"message": "Transport method does not exist."})

        update_fields = {k: v for k, v in transport.model_dump().items() if v is not None}

        if update_fields:
            collection.update_one({"name": transport_type}, {"$set": update_fields})
            return JSONResponse(status_code=200, content={"message": f"Transport method {transport_type} updated successfully"})
        else:
            return JSONResponse(status_code=400, content={"message": "No fields to update"})

    else:
        if exists:
            return JSONResponse(status_code=400, content={"message": "Transport method already exists. Use edit flag to update"})
        collection.insert_one(transport.model_dump())
        return JSONResponse(status_code=200, content={"message": f"Transport method {transport_type} added successfully"})

@router.delete("/delete_transport_method") #Admin only
async def delete_transport_method(transport_type: str, admin_password: str = Header(None)): #Last tested, 13/02/2025
    "Deletes a transport method upon the request of an admin"
    actual_password = os.getenv("ADMIN_PASSWORD")

    if admin_password != actual_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can delete transport methods. Go away."})
    
    database_name = "transports"
    collection_name = "transport_methods"

    if collection_name not in mongo_client[database_name].list_collection_names():
        return JSONResponse(status_code=404, content={"message": f"Collection {collection_name} not found in database {database_name}"})
    
    collection = mongo_client[database_name][collection_name]
    exists = collection.find_one({"name": transport_type})

    if not exists:
        return JSONResponse(status_code=404, content={"message": f"Transport method {transport_type} not found. Ensure spell check."})

    collection.delete_one({"name": transport_type})
    return JSONResponse(status_code=200, content={"message": f"Transport method {transport_type} deleted successfully"})
    
@router.get("/weight_converter_sanity_check")
async def weight_converter_sanity_check():
    """This function checks if every good is either measured in KG or their unit has a conversion formula to KG."""
    db = mongo_client["outposts"]
    collection = db["goods"]

    # Convert weight_unit_conversion_table into a set for O(1) lookup
    conversion_set = {(entry["name"], entry["unit"]) for entry in weight_unit_conversion_table}

    goods = collection.find({}, {"name": 1, "unit": 1})  # Fetch only required fields

    errors = []
    
    for good in goods:
        name, unit = good.get("name"), good.get("unit")

        # Direct kg check
        if unit == "kg":
            continue

        # Check if the name and unit exist in the conversion table
        if (name, unit) not in conversion_set:
            errors.append(f"Missing conversion for {name} ({unit})")

    if errors:
        return JSONResponse(
            status_code=500,
            content={"message": "Weight converter issues found", "errors": errors}
        )

    return JSONResponse(status_code=200, content={"message": "Weight converter is working fine"})



# List all transport options
@router.get("/")
async def list_transport(): #Last tested. 13/02/2025
    """Lists all transport methods available along with their details"""
    database_name = "transports"
    collection_name = "transport_methods"

    if collection_name not in mongo_client[database_name].list_collection_names():
        return JSONResponse(status_code=404, content={"message": f"Collection {collection_name} not found in database {database_name}"})
    
    collection = mongo_client[database_name][collection_name]

    transports = list(collection.find({}, {"_id": 0}))
    if not transports:
        return JSONResponse(status_code=404, content={"message": "No transport methods found"})
    
    return JSONResponse(status_code=200, content={"transports": transports})

@router.get("/transport_profile") #Tested. 12/02/2025 (Pre-pre-valentine's day)
async def transport_profile(user_id: str):
    result = {}
    database_name = "users"
    collection_name = "metaverse_users"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "{collection_name} Collection not found"})

    collection = db[collection_name]
    user = collection.find_one({"username": user_id})

    if not user:
        return JSONResponse(status_code=200, content={"message": "User {user_id} not found"})
    
    #Weight calculation
    # result["weight"] = user["merchandise_weight"]

    #Distance calculation
    current_outpost = user["current_outpost_id"]
    print(current_outpost)
    if current_outpost is None:
        return JSONResponse(status_code=200, content={"message": "User {user_id} has no current outpost. Choose spawn point."})
    
    database_name = "outposts"
    collection_name = "spawn_points"

    db = mongo_client[database_name]
    outpost_collection = db["spawn_points"]
    # print("Total spawn points", outpost_collection.count_documents({}))

    routes = outpost_collection.find_one({"id": current_outpost}, {"trade_routes": 1, "latitude": 1, "longitude": 1})
    print(routes)
    if not routes or "trade_routes" not in routes:
        return JSONResponse(status_code=200, content={"message": "No trade routes found for current outpost. You are stranded."})

    trade_routes = routes["trade_routes"]
    current_coords = (routes["latitude"], routes["longitude"])
    print(current_coords)
    # print(trade_routes)
    connected_outposts = list(
        outpost_collection.find(
            {"id": {"$in": trade_routes}}, 
            {"_id": 0, "id": 1, "latitude": 1, "longitude": 1}
        )
    )
    routes = [
            {**outpost, "distance": direct_distance_calculator(current_coords, (outpost["latitude"], outpost["longitude"]))}
            for outpost in connected_outposts
        ]
    result["merchandise_weight"] = user["merchandise_weight"]
    result["routes"] = routes

    return JSONResponse(status_code=200, content=result)

# Get transport details
@router.get("/{transport_id}")
async def get_transport(transport_id: int):
    return JSONResponse(status_code=200, content={"transport_id": transport_id, "type": "Caravan", "fee": 100})
