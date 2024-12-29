from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Get all users
@router.get("/")
async def get_users():
    return {"users": ["John Doe", "Jane Smith"]}

# Create a user
@router.post("/")
async def create_user(user: dict):
    return {"message": "User created", "user": user}

# Get a user by ID
@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "Sample User"}
