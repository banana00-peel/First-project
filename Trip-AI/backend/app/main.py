"""FastAPI 主应用"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import auth, share, trips
from app.config import get_settings
from app.core.db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # 预热高德 MCP 工具；失败不阻塞启动，首次请求会按需重试
    try:
        from app.services.amap_mcp import get_amap_tools
        await get_amap_tools()
    except Exception:
        logger.warning("高德 MCP 工具预热失败（应用仍可启动，首次请求会重试）")
    yield
    from app.services.amap_mcp import close_amap_mcp
    await close_amap_mcp()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 旅行规划平台 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(trips.router, prefix="/api")
app.include_router(share.router, prefix="/api")


@app.get("/")
def root():
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.app_name, "version": settings.app_version}
