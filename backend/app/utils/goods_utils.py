from pydantic import BaseModel, Field, field_validator
import datetime

class Good(BaseModel):
    id: str | None = None
    good_name: str
    good_description: str | None = None
    good_price: int = Field(gt=0)
    good_quantity: int = Field(gt=0)
    outpost_id: str
    last_updated: datetime.datetime | None = None

    @field_validator("id", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        return v if v != "" else None


