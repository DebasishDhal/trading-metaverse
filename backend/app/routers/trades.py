from fastapi import APIRouter

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
