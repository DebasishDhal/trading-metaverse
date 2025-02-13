from typing import List
from geopy.distance import geodesic
from pydantic import Field
# import networkx as nx

from pydantic import BaseModel
from typing import Optional
#import optional

class Transport(BaseModel):
    name: str
    speed: Optional[int] = Field(None, gt=0)
    capacity: Optional[int] = Field(None, gt=0)
    base_cost_per_km: Optional[int] = Field(None, gt=0)
    edit: bool = False

weight_unit_conversion_table = [
    {
        "name": "Silk",
        "unit": "meter",
        "per_unit_mass": 0.04 #40 grams/meter
    },
    {
        "name": "Gems",
        "unit": "carat",
        "per_unit_mass": 0.0002
    },
    {
        "name": "Textiles",
        "unit": "meter",
        "per_unit_mass": 0.15
    },
    {
        "name": "Gold",
        "unit": "ounce",
        "per_unit_mass": 0.028
    },
    {
        "name": "Paper",
        "unit": "sheet",
        "per_unit_mass": 0.005
    },
    {
        "name": "Glassware", #Assume a glass cup
        "unit": "piece",
        "per_unit_mass": 0.3
    },
    {
        "name": "Perfume",
        "unit": "bottle",
        "per_unit_mass": 0.2 #Assuming a 100ml bottle
    },
    {
        "name": "Cotton",
        "unit": "meter",
        "per_unit_mass": 0.15
    },
    {
        "name": "Lacquerware",
        "unit": "piece",
        "per_unit_mass": 0.05 #50 gms
    },
    {
        "name": "Porcelain",
        "unit": "piece",
        "per_unit_mass": 0.250 #250 gms
    },
    {
        "name": "Timber",
        "unit": "meter",
        "per_unit_mass": 15
    },
    {
        "name": "Wine",
        "unit": "liter",
        "per_unit_mass": 1 #for trade purposes, I'll keep it at 1.
    },
    {
        "name": "Honey",
        "unit": "liter",
        "per_unit_mass": 1.4
    }
]


def direct_distance_calculator(coords1, coords2):
    return round(geodesic(coords1, coords2).km, 1)