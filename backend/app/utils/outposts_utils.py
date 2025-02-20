from pydantic import BaseModel, Field
from typing import List, Optional

class SpawnPoint(BaseModel):
    id: str = Field(..., description="Unique ID for the spawn point")
    name: str = Field(..., description="Name of the spawn point")
    region: str = Field(..., description="Region of the spawn point")
    description: str = Field(..., description="Description of the spawn point")
    gold_bonus: int = Field(..., ge=0, description="Gold bonus for the spawn point")
    reputation_bonus: int = Field(..., ge=0, description="Reputation bonus for the spawn point")
    trade_routes: List[str] = Field(..., description="List of connected trade routes")
    latitude: float = Field(..., description="Latitude of the spawn point")
    longitude: float = Field(..., description="Longitude of the spawn point")
    era: str = Field(..., description="Era of the spawn point")
    economy_type: str = Field(..., description="Economy type")
    population: int = Field(..., ge=0, description="Population at the spawn point")
    language: List[str] = Field(..., description="Languages spoken at the spawn point")
    culture: str = Field(..., description="Culture of the spawn point")
    climate: str = Field(..., description="Climate of the spawn point")
    goods_available: Optional[List[dict]] = Field(default=[], description="List of goods available")
    goods_demanded: Optional[List[dict]] = Field(default=[], description="List of goods demanded")

class FetchSpawnPoint(BaseModel):
    username: str = Field(..., description="Username of the user")
    spawn_id: str = Field(..., description="ID of the spawn point")

class DeleteSpawnPoint(BaseModel):
    spawn_id: str = Field(..., description="ID of the spawn point")
    admin_password: str = Field(..., description="ADMIN Password for outpost deletion")