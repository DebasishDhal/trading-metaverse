from fastapi import APIRouter, Header, UploadFile, File, Form
from backend.app.utils.mongo_utils import mongo_client
from backend.app.utils.transports_utils import weight_unit_conversion_table, direct_distance_calculator, Transport
from fastapi.responses import JSONResponse
import gpxpy
from geopy.distance import geodesic
import os
import pandas as pd

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

@router.post("/add_route") #Admin only
async def add_route(file_path: str, start: str, end: str, admin_password: str = Header(None)):
    """Add coordinate of routes from one outpost to another. 
    Input - relative file path of gpx file manually added from google maps
    Output - list of coordinates for every route in MongoDB
    Challenge - There is no direct route from Tobolsk to Hanzhou on modern google maps, I had to make two separate roads, one from Tobolsk to Mongolia, and another from Mongolia to Hanzhou."""

    actual_password = os.getenv("ADMIN_PASSWORD")

    if admin_password != actual_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can add routes. Go away."})
    
    # if not os.path.isfile(file_path):
    #     return JSONResponse(status_code=404, content={"message":"File not found"})

    database_name = "transports"
    collection_name = "routes"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)

    routes_collection = db[collection_name]

    database_name = "outposts"
    collection_name = "spawn_points"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "{collection_name} Collection not found"})
    
    outpost_collection = db[collection_name]
    source_doc = outpost_collection.find_one({"name": start})
    destination_doc = outpost_collection.find_one({"name": end})

    if not source_doc or not destination_doc:
        return JSONResponse(status_code=404, content={"message": "Source or destination not found"})
    
    source_id = source_doc["id"]
    destination_id = destination_doc["id"]

    point_count = 100
    if file_path.endswith(".gpx"):
        try:
            with open(file_path, "r") as f:
                gpx = gpxpy.parse(f)

            lats, lons = [], []

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        lats.append(point.latitude)
                        lons.append(point.longitude)

            zipped_route = list(zip(lats, lons))
            total_distance = 0
            for i in range(1, len(zipped_route)):
                total_distance += geodesic(zipped_route[i-1], zipped_route[i]).kilometers

            step = len(lats) // point_count

            final_lats, final_lons = [], []
            for i in range(0, len(lats), step):
                final_lats.append(lats[i])
                final_lons.append(lons[i])

            if lats[-1] != final_lats[-1]:
                final_lats.append(lats[-1])
                final_lons.append(lons[-1])
            
            print(len(final_lats), len(final_lons))            

            print(start, end)
            zipped_route = list(zip(final_lats, final_lons))

            # Check for existing route in both directions
            existing_route = routes_collection.find_one(
                {"$or": [
                    {"source": start, "destination": end},
                    {"source": end, "destination": start}
                ]}
            )

            if existing_route:
                return JSONResponse(status_code=400, content={"message": "Route already exists. Cannot insert duplicate."})
            
            # Insert the new route
            result = routes_collection.insert_one(
                {
                    "source": start,
                    "source_id": source_id,
                    "destination": end,
                    "destination_id": destination_id,
                    "route": zipped_route,
                    "distance": round(total_distance, 1)
                }
            )

            if result.inserted_id is not None:
                return JSONResponse(status_code=201, content={"message": "Route added successfully."})
            else:
                return JSONResponse(status_code=500, content={"message": "Failed to add route."})
                
        except Exception as e:
            return JSONResponse(status_code=500, content={"message": str(e)})
        
    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)

        sliced_df = df.iloc[start:end]
        data = sliced_df.to_dict(orient='records')
        zipped_route = list(zip(data["latitude"], data["longitude"]))
    
        total_distance = 0
        for i in range(1, len(zipped_route)):
            total_distance += geodesic(zipped_route[i-1], zipped_route[i]).kilometers

        result = routes_collection.insert_one({
            "source": start,
            "source_id": source_id,
            "destination": end,
            "destination_id": destination_id,
            "route": zipped_route,
            "distance": total_distance})

        if result.inserted_id is not None:
            return JSONResponse(status_code=201, content={"message": "Route added successfully."})
        else:
            return JSONResponse(status_code=500, content={"message": "Failed to add route."})
        
        # collection.insert_many(data)

    elif os.path.isdir(file_path):
        gpx_files = sorted([file for file in os.listdir(file_path) if file.endswith(".gpx")])
        print(gpx_files)

        lats, lons = [], []
        for gpx_file in gpx_files:
            gpx_file_path = os.path.join(file_path, gpx_file)
            with open(gpx_file_path, "r") as f:
                gpx = gpxpy.parse(f)

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        lats.append(point.latitude)
                        lons.append(point.longitude)

        step = len(lats) // point_count

        final_lats, final_lons = [], []
        for i in range(0, len(lats), step):
            final_lats.append(lats[i])
            final_lons.append(lons[i])
        
        if lats[-1] != final_lats[-1]:
            final_lats.append(lats[-1])
            final_lons.append(lons[-1])
        
        zipped_route = list(zip(final_lats, final_lons))

        total_distance = 0
        for i in range(1, len(zipped_route)):
            total_distance += geodesic(zipped_route[i-1], zipped_route[i]).kilometers

        route = {
            "source": start,
            "source_id": source_id,
            "destination": end,
            "destination_id": destination_id,
            "route": zipped_route,
            "distance": total_distance
        }

        result = routes_collection.insert_one(route)

        if result.inserted_id is not None:
            return JSONResponse(status_code=201, content={"message": "Route added successfully."})
        else:
            return JSONResponse(status_code=500, content={"message": "Failed to add route."})

    else:
        return JSONResponse(status_code=400, content={"message": "Invalid file format"})
        

@router.post("/small_tasks_route")
async def small_tasks(admin_password: str = Header(None)):

    actual_password = os.getenv("ADMIN_PASSWORD")
    if admin_password != actual_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can use this. Go away."})

    database_name = "transports"
    collection_name = "routes"

    db = mongo_client[database_name]
    if collection_name not in db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": f"{collection_name} Collection not found"})  # Use f-string for interpolation
    
    routes_collection = db[collection_name]

    # For every doc, take the "route" field, calculate the distance and update the "distance" field
    for doc in list(routes_collection.find()):
        print("Inside loop")
        if "route" not in doc:
            continue

        route = doc["route"]
        total_distance = 0
        for i in range(1, len(route)):
            total_distance += geodesic(route[i-1], route[i]).kilometers
        
        routes_collection.update_one({"_id": doc["_id"]}, {"$set": {"distance": round(total_distance, 2)}})
        
    return JSONResponse(status_code=200, content={"message": "All routes updated successfully"})