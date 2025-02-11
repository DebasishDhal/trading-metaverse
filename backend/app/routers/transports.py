from fastapi import APIRouter
from backend.app.utils.mongo_utils import mongo_client
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/transports",
    tags=["Transports"]
)

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
    
@router.get("/weight_converter_sanity_check")
async def weight_converter_sanity_check():
    db = mongo_client["outposts"]
    collection = db["goods"]

    # Convert weight_unit_conversion_table into a set for O(1) lookup
    conversion_set = {(entry["name"], entry["unit"]) for entry in weight_unit_conversion_table}

    goods = collection.find({}, {"name": 1, "unit": 1})  # Fetch only required fields

    errors = []
    
    for good in goods:
        name, unit = good.get("name"), good.get("unit")

        # Direct kg check
        if unit == "kg":
            continue

        # Check if the name and unit exist in the conversion table
        if (name, unit) not in conversion_set:
            errors.append(f"Missing conversion for {name} ({unit})")

    if errors:
        return JSONResponse(
            status_code=500,
            content={"message": "Weight converter issues found", "errors": errors}
        )

    return JSONResponse(status_code=200, content={"message": "Weight converter is working fine"})



# List all transport options
@router.get("/")
async def list_transport():
    return {"options": ["Caravan", "Fast Horse"]}

# Get transport details
@router.get("/{transport_id}")
async def get_transport(transport_id: int):
    return {"transport_id": transport_id, "type": "Caravan", "fee": 100}
