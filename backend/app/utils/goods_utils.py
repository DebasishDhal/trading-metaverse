from pydantic import BaseModel, Field
import datetime

class Good(BaseModel):
    id: str | None = None
    good_name: str
    good_description: str | None = None
    good_price: int = Field(gt=0)
    good_quantity: int = Field(gt=0)
    outpost_id: str
    last_updated: datetime.datetime | None = None


