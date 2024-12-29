from fastapi import APIRouter

router = APIRouter(
    prefix="/transports",
    tags=["Transports"]
)

# List all transport options
@router.get("/")
async def list_transport():
    return {"options": ["Caravan", "Fast Horse"]}

# Get transport details
@router.get("/{transport_id}")
async def get_transport(transport_id: int):
    return {"transport_id": transport_id, "type": "Caravan", "fee": 100}
