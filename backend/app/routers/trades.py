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
    #First we check through all the conditions that might generate errors, then we do the transaction
    """
    Deducts good's quantity from outposts/goods (field "quantity") and outposts/spawn_points ("goods_available"), 
    Increases good's quantity in player's inventory ("inventory").
    Deducts money from player's money
    Adds trade ID in trades/purchases collection

    Parameters:
    - good_id: good which needs to be purchased
    - username: Player who will purchase
    - quantity: Quantity of good which needs to be purchased
    - outpost_id: Outpost where the good is available

    Returns:
    - JSONResponse: A response indicating the success or failure of the operation.

    Notes:
    - The goods in users inventory is stored as a list. The last purchased quantity will come out as the top item in the inventory list, acts as a cache.
    """

    outpost_db = mongo_client["outposts"]
    goods_collection = outpost_db["goods"]
    outposts_collection = outpost_db["spawn_points"]

    outpost = outposts_collection.find_one({"id": outpost_id})
    if not outpost:
        return JSONResponse(status_code=404, content={"message": f"Outpost with ID {outpost_id} not found"})

    good = goods_collection.find_one({"name": good_id, "outpost_id": outpost_id})
    if not good:
        return JSONResponse(status_code=404, content={"message": f"Good with ID {good_id} not found in outpost {outpost_id}"})

    available_quantity = good["quantity"]
    if quantity > available_quantity:
        return JSONResponse(status_code=400, content={"message": f"Insufficient quantity of good with ID {good_id} in outpost {outpost_id}"})
    
    money_required = quantity * good["price"]

    #Check if the player has enough money
    player_db = mongo_client["users"]
    player_collection = player_db["metaverse_users"]

    player = player_collection.find_one({"username": username})
    if not player:
        return JSONResponse(status_code=404, content={"message": f"Player with username {username} not found"})
    if player.get("current_outpost_id") != outpost_id:
        return JSONResponse(status_code=400, content={"message": f"Player is not in outpost {outpost_id}"})
    if player.get("money", 0) < money_required:
        return JSONResponse(status_code=400, content={"message": f"Not enough funds. Required: {money_required}, Available: {player.get('money',0)}"})
    
    goods_available = outpost.get("goods_available", [])

    updated_good = None
    for good in goods_available:
        if good["name"] == good_id:
            if good["quantity"] < quantity:
                return JSONResponse(status_code=400, content={"message": f"Insufficient quantity of good '{good_id}' in spawn point {outpost_id}"})
            good["quantity"] -= quantity
            updated_good = good
            break

    if not updated_good:
        return JSONResponse(status_code=404, content={"message": f"Good '{good_id}' not found in spawn point {outpost_id}"})

    # Reorder the list (move updated good to the top)
    goods_available = [updated_good] + [good for good in goods_available if good["name"] != good_id]

    # Update the spawn_points collection
    outposts_collection.update_one(
        {"id": outpost_id},
        {"$set": {"goods_available": goods_available}}
    )

    player_inventory_now = player.get("inventory", {})
    time_now = datetime.datetime.now()
    if good_id not in player_inventory_now: #Do not use dict get method here, as it doesn't update anything
        player_inventory_now[good_id] = {"quantity": 0, "average_price": 0, "updated_at": time_now, "created_at": time_now}

    previous_quantity = player_inventory_now[good_id]["quantity"]
    previous_average_price = player_inventory_now[good_id]["average_price"]

    new_quantity = previous_quantity + quantity
    average_price = (previous_quantity * previous_average_price + money_required) / new_quantity

    trade_id = uuid.uuid4().hex

    time = datetime.datetime.now()
    player_inventory_now[good_id].update({
    "quantity": new_quantity,
    "average_price": average_price,
    "updated_at": time,
    "trade_ids": player_inventory_now[good_id].get("trade_ids", []) + [trade_id]
    }) #Do not use get method, it won't update anything.

    player_collection.update_one({"username": username}, {"$set": {"inventory": player_inventory_now, "money": player.get("money", 0) - money_required}})

    #Update the good quantity in the outpost
    goods_collection.update_one({"name": good_id, "outpost_id": outpost_id}, {"$set": {"quantity": available_quantity - quantity}})

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
        "type": "purchase",
        "price": money_required,
        "created_at": time_now
    }

    trade_collection.insert_one(trade_data)


    ##TODO -- Add trade id, player id, trade details to trade database. Done
    ##TODO -- Check outpost_id of good and username are the same. Done

    return JSONResponse(status_code=200, content={"message": f"Successfully bought {quantity} of good with ID {good_id} in outpost {outpost_id}"})

@router.post("/sell_goods") #Tested
async def sell_goods(username:str, good_id: str, quantity: int, outpost_id: str, price: float, unit: str):
    """
        Takes username, good_id, quantity, outpost_id, price, unit as input.
        Deducts quantity from user.inventory
        Increases quantity at outposts.spawn_points.goods_available
        Increases quantity at outpost.goods.quantity

        Needs more polishing TODO
    """
    ## TODO - Figure out the goddamn price. First user should be able to query about the price he might get, then only sell.
    ## TODO - Do a separate endpoint for price query from the outpost.
    if quantity <= 0:
        return JSONResponse(status_code=400, content={"message": "Quantity must be greater than 0"})
    outposts_db = mongo_client["outposts"]
    goods_collection = outposts_db["goods"]
    outposts_collection = outposts_db["spawn_points"]
    users_db = mongo_client["users"]
    users_collection = users_db["metaverse_users"]
    trade_database = mongo_client["trades"]
    trade_collection = trade_database["purchases"]
    
    user = users_collection.find_one({"username": username, "current_outpost_id": outpost_id})

    if not user:
        return JSONResponse(status_code=404, content={"message": f"User with username {username} not found at {outpost_id}"})
    
    time = datetime.datetime.now()
    trade_id = uuid.uuid4().hex

    inventory = user.get("inventory", {})
    if good_id not in inventory:
        return JSONResponse(status_code=404, content={"message": f"Good with ID {good_id} not found in inventory"})
    
    if quantity > inventory[good_id]["quantity"]:
        return JSONResponse(status_code=400, content={"message": f"Insufficient quantity of good with ID {good_id} in inventory"})
    
    goods_result = goods_collection.update_one({"name": good_id, "outpost_id": outpost_id}, {"$inc": {"quantity": quantity}})

    #From the player inventory, deduct the quantity of the good
    inventory[good_id]["quantity"] -= quantity
    inventory[good_id]["updated_at"] = time
    inventory[good_id]["trade_ids"] = inventory[good_id].get("trade_ids", []) + [trade_id]
    users_collection.update_one({"username": username, "current_outpost_id": outpost_id}, {"$set": {"inventory": inventory}})

    #Update the spawn_points collection
    result = outposts_collection.update_one(
        {"id": outpost_id, "goods_available.name": good_id},  # Match document containing the good
        {
            "$inc": {"goods_available.$.quantity": quantity},  # Increment quantity if it exists
            "$set": {"goods_available.$.price": price, "goods_available.$.unit": unit}
        }
    )

    # If no document was modified, the good doesn't exist; insert it
    if result.matched_count == 0:
        result = outposts_collection.update_one(
            {"id": outpost_id},  # Match the specific outpost
            {
                "$push": {  # Add a new good dictionary to the goods_available array
                    "goods_available": {
                        "name": good_id,
                        "price": price,
                        "quantity": quantity,
                        "unit": unit
                    }
                }
            }
        )

    trade_entry = {
        "trade_id": trade_id,
        "username": username,
        "good_id": good_id,
        "quantity": quantity,
        "outpost_id": outpost_id,
        "type": "sell",
        "price": price,
        "created_at": time
    }

    trade_collection.insert_one(trade_entry)
    
    return JSONResponse(status_code=200, content={"message": f"Successfully sold {quantity} of good with ID {good_id} in outpost {outpost_id}"})

