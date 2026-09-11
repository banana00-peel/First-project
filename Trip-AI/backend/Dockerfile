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

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
