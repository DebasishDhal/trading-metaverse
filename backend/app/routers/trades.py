from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.utils.mongo_utils import mongo_client

import datetime, uuid
router = APIRouter(
    prefix="/trades",
    tags=["Trades"]
)

# List all trades
@router.get("/")
async def list_trades():
    return {"trades": ["Trade 1", "Trade 2"]}

# Create a trade
@router.post("/")
async def create_trade(trade: dict):
    return {"message": "Trade created in backend.app.router.trades", "trade": trade}

@router.get("/fetch/{outpost}")
async def fetch_goods(outpost: str):
    db = mongo_client["outposts"]
    collection = db["goods"]

    goods = list(collection.find({"outpost_id": outpost}))
    
    if not goods:
        return JSONResponse(status_code=404, content={"message":"No goods found for this outpost"})
    
    return JSONResponse(status_code=200, content={"outpost": outpost, "goods": str(goods)})


@router.post("/purchase_goods")
async def purchase_goods(username:str, good_id: str, quantity: int, outpost_id: str):
    #First check whether the good exists in that outpost or not
    outpost_db = mongo_client["outposts"]
    outpost_collection = outpost_db["goods"]

    good = outpost_collection.find_one({"id": good_id, "outpost_id": outpost_id})
    if not good:
        return JSONResponse(status_code=404, content={"message": f"Good with ID {good_id} not found in outpost {outpost_id}"})

    available_quantity = good["good_quantity"]
    if quantity > available_quantity:
        return JSONResponse(status_code=400, content={"message": f"Insufficient quantity of good with ID {good_id} in outpost {outpost_id}"})
    
    money_required = quantity * good["good_price"]

    #Check if the player has enough money
    player_db = mongo_client["users"]
    player_collection = player_db["metaverse_users"]

    player = player_collection.find_one({"username": username})
    if not player:
        return JSONResponse(status_code=404, content={"message": f"Player with username {username} not found"})
    
    if player.get("money", 0) < money_required:
        return JSONResponse(status_code=400, content={"message": f"Not enough funds. Required: {money_required}, Available: {player.get('money',0)}"})
    
    player_inventory_now = player.get("inventory", {})
    if good_id not in player_inventory_now: #Do not use dict get method here, as it doesn't update anything
        player_inventory_now[good_id] = {"quantity": 0, "average_price": 0, "updated_at": None, "created_at": datetime.datetime.now()}

    previous_quantity = player_inventory_now[good_id]["quantity"]
    previous_average_price = player_inventory_now[good_id]["average_price"]

    new_quantity = previous_quantity + quantity
    average_price = (previous_quantity * previous_average_price + money_required) / new_quantity

    trade_id = uuid.uuid4().hex

    player_inventory_now[good_id].update({
    "quantity": new_quantity,
    "average_price": average_price,
    "updated_at": datetime.datetime.now(),
    "trade_ids": player_inventory_now[good_id].get("trade_ids", []) + [trade_id]
    }) #Do not use get method, it won't update anything.

    player_collection.update_one({"username": username}, {"$set": {"inventory": player_inventory_now, "money": player.get("money", 0) - money_required}})

    #Update the good quantity in the outpost
    outpost_collection.update_one({"id": good_id, "outpost_id": outpost_id}, {"$set": {"good_quantity": available_quantity - quantity}})

    trade_database = mongo_client["trades"]
    trade_collection_name = "purchases"

    if trade_collection_name not in trade_database.list_collection_names():
        trade_database.create_collection(trade_collection_name)
    
    trade_collection = trade_database[trade_collection_name]

    trade_data = {
        "trade_id": trade_id,
        "username": username,
        "good_id": good_id,
        "quantity": quantity,
        "outpost_id": outpost_id,
        "created_at": datetime.datetime.now()
    }

    trade_collection.insert_one(trade_data)

    ##TODO -- Add trade id, player id, trade details to trade database. Done
    ##TODO -- Check outpost_id of good and username are the same. Done

    return JSONResponse(status_code=200, content={"message": f"Successfully bought {quantity} of good with ID {good_id} in outpost {outpost_id}"})
