FROM python:3.11-slim

WORKDIR /app

# 安装 Node.js 并全局预装高德官方 MCP 服务器（@amap/amap-maps-mcp-server）。
# 后端通过 `npx` 拉起该 MCP 子进程取数，故运行镜像需含 Node 环境。
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @amap/amap-maps-mcp-server \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 以非 root 用户运行：创建专用用户并切换，避免容器内进程以 root 身份运行
RUN useradd --create-home --uid 10001 appuser
# /app 只读无需写 .pyc；HOME 指向可写目录（worker 里 npx 拉 MCP 子进程需要可写缓存）
ENV PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/appuser

USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
