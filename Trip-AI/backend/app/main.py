"""FastAPI 主应用"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, share, trips
from app.config import get_settings
from app.core.db import init_db
from app.core.errors import install_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 行程生成已移至 Celery worker，web 进程只入队 + 轮询，无需再预热/关闭 MCP
    setup_logging()
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 旅行规划平台 API",
    lifespan=lifespan,
)

install_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求上下文：生成/透传 X-Request-ID，供日志与错误响应关联（最外层）
app.add_middleware(RequestContextMiddleware)

app.include_router(auth.router, prefix="/api")
app.include_router(trips.router, prefix="/api")
app.include_router(share.router, prefix="/api")


@app.get("/")
def root():
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.app_name, "version": settings.app_version}
