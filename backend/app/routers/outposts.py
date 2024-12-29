from fastapi import APIRouter

router = APIRouter(
    prefix="/outposts",
    tags=["Outposts"]
)

# List all outposts
@router.get("/")
async def list_outposts():
    return {"outposts": ["Siberian Frontier", "Indian Bazar", "Arab Souk"]}

# Get details of a specific outpost
@router.get("/{outpost_id}")
async def get_outpost(outpost_id: int):
    return {"outpost_id": outpost_id, "name": "Sample Outpost", "language": "Russian"}
