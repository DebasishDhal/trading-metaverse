from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
import os
from backend.app.utils.mongo_utils import mongo_client

router = APIRouter(
    prefix="/backup",
    tags=["Backup"]
)

#Route through which you can simply enter database name and collection name to get all the data in that collection
@router.get("/backup_collection")
async def backup_collection(database_name: str, collection_name: str, admin_password: str = Header(None)):
    actual_password = os.getenv("ADMIN_PASSWORD")
    
    if admin_password != actual_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can backup data. Go away."})
    
    source_db = mongo_client[database_name]
    source_collection = source_db[collection_name]  

    data = list(source_collection.find())

    target_db_name = "backup"
    target_collection_name = f"{database_name}**{collection_name}"

    if target_collection_name in mongo_client[target_db_name].list_collection_names():
        mongo_client[target_db_name].drop_collection(target_collection_name)

    target_collection = mongo_client[target_db_name][target_collection_name]
    target_collection.insert_many(data)

    return JSONResponse(status_code=200, content={"message": f"Collection {collection_name} backed up successfully"})


@router.get("/restore_collection")
async def restore_collection(database_name: str, collection_name: str, admin_password: str = Header(None)):
    actual_password = os.getenv("ADMIN_PASSWORD")

    if admin_password != actual_password:
        return JSONResponse(status_code=403, content={"message": "Only admins can restore data. Go away."})
    
    source_db = mongo_client["backup"]
    source_collection_name = f"{database_name}**{collection_name}"

    if source_collection_name not in source_db.list_collection_names():
        return JSONResponse(status_code=404, content={"message": "Backup not found"})
    
    source_collection = source_db[source_collection_name]

    data = list(source_collection.find())

    target_db = mongo_client[database_name]
    target_collection = target_db[collection_name]

    target_collection.delete_many({})

    target_collection.insert_many(data)

    return JSONResponse(status_code=200, content={"message": f"Collection {collection_name} of database {database_name} restored successfully"})