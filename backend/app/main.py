from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import ads, agents, config, dashboard, finance, memory, outreach, reports, social, tasks
from app.api.websocket import router as ws_router
from app.core.redis_client import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up Redis connection
    await get_redis()
    yield
    # Shutdown: close Redis
    await close_redis()


app = FastAPI(
    title="Polsia AI Business Agent",
    description="Autonomous AI platform that runs your company 24/7",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routes
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")
app.include_router(social.router, prefix="/api/v1")
app.include_router(outreach.router, prefix="/api/v1")
app.include_router(ads.router, prefix="/api/v1")
app.include_router(finance.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

# WebSocket
app.include_router(ws_router)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
