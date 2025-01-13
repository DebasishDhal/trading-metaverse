from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from .routers import users, outposts, trades, transports
from backend.app.routers import users, outposts, trades, transports, auth, goods, trades

app = FastAPI(
    title="Trading Outpost API",
    description="API for managing trading outposts, users, and trades in the Trading Outpost game.",
    version="1.0.0"
)

# CORS Setup (to allow React frontend in future)
origins = [
    "http://localhost:3000",  # React frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router)
app.include_router(outposts.router)
app.include_router(trades.router)
app.include_router(users.router)
app.include_router(transports.router)
app.include_router(goods.router)
app.include_router(trades.router)

# Test route
@app.get("/")
async def root():
    return {"message": "Welcome to the Trading Outpost API"}