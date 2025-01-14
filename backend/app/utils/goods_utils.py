from pydantic import BaseModel, Field, field_validator
import datetime

class Good(BaseModel):
    # id: str | None = None
    name: str
    # description: str | None = None
    price: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit: str
    outpost_id: str
    last_updated: datetime.datetime | None = None

    # @field_validator("id", mode="before")
    # @classmethod
    # def empty_string_to_none(cls, v):
    #     return v if v != "" else None


