from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import bot, trades, risk, health, legacy, auth, charts, sockets, admin, support
from app.storage.db import init_db
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS - Allow all for network development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, # Note: if allow_origins is "*", many browsers block credentials. 
                            # But since we use Bearer, it's fine.
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Include Routers
app.include_router(bot.router, prefix=f"{settings.API_V1_STR}/bot", tags=["bot"])
app.include_router(trades.router, prefix=f"{settings.API_V1_STR}/trades", tags=["trades"])
app.include_router(risk.router, prefix=f"{settings.API_V1_STR}/risk", tags=["risk"])
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["health"])
app.include_router(charts.router, prefix=f"{settings.API_V1_STR}/charts", tags=["charts"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(legacy.router, prefix=f"{settings.API_V1_STR}/legacy", tags=["legacy"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(support.router, prefix=f"{settings.API_V1_STR}/support", tags=["support"])
app.include_router(sockets.router, tags=["sockets"]) # Sockets usually at /ws
