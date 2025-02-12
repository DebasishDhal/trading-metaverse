from fastapi import APIRouter
from backend.app.utils.mongo_utils import mongo_client
from backend.app.utils.transports_utils import weight_unit_conversion_table, weight_calculator
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/transports",
    tags=["Transports"]
)
    
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
async def list_transport():
    return JSONResponse(status_code=200, content={"options": ["Caravan", "Fast Horse"]})

@router.get("/transport_profile")
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
    inventory = [{"name" : key, **value} for key, value in user["inventory"].items()]
    total_weight = weight_calculator(inventory)
    result["weight"] = total_weight

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

    routes = outpost_collection.find_one({"id": current_outpost}, {"trade_routes": 1})
    print(routes)
    if not routes or "trade_routes" not in routes:
        return JSONResponse(status_code=200, content={"message": "No trade routes found for current outpost. You are stranded."})

    trade_routes = routes["trade_routes"]
    # print(trade_routes)
    connected_outposts = list(
        outpost_collection.find(
            {"id": {"$in": trade_routes}}, 
            {"_id": 0, "id": 1, "latitude": 1, "longitude": 1}
        )
    )

    return connected_outposts

# Get transport details
@router.get("/{transport_id}")
async def get_transport(transport_id: int):
    return JSONResponse(status_code=200, content={"transport_id": transport_id, "type": "Caravan", "fee": 100})
