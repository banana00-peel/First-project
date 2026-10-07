"""FastAPI 主应用"""
from contextlib import asynccontextmanager

import redis
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import auth, share, trips
from app.config import get_settings
from app.core.db import engine, get_db, init_db
from app.core.errors import install_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.ratelimit import limiter

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 行程生成已移至 Celery worker，web 进程只入队 + 轮询，无需再预热/关闭 MCP
    setup_logging()
    init_db()
    yield
    # 优雅关停：释放数据库连接池，避免进程退出时遗留挂起连接
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 旅行规划平台 API",
    lifespan=lifespan,
)

install_exception_handlers(app)

# slowapi 限流器挂到 app.state，路由上的 @limiter.limit 装饰器据此生效
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    # 方法与请求头收成显式白名单（不放行 *），只开放前端实际用到的，减小攻击面。
    # X-Request-ID 由 RequestContextMiddleware 透传，需放行。
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID", "Accept"],
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


def _check_database(db: Session) -> None:
    db.execute(text("SELECT 1"))


def _check_redis() -> None:
    client = redis.Redis.from_url(
        settings.redis_url, socket_connect_timeout=2, socket_timeout=2
    )
    try:
        client.ping()
    finally:
        client.connection_pool.disconnect()


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    """就绪探针：DB 与 Redis 均可达返回 200，否则 503。

    与 /health（纯存活）区分：依赖未就绪时返回 503，供编排层判定 healthy = ready。
    """
    checks: dict[str, str] = {}
    try:
        _check_database(db)
        checks["database"] = "ok"
    except Exception as e:  # noqa: BLE001 —— 就绪探测需捕获一切依赖异常
        checks["database"] = str(e)
    try:
        _check_redis()
        checks["redis"] = "ok"
    except Exception as e:  # noqa: BLE001
        checks["redis"] = str(e)
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "not_ready", "checks": checks},
    )
