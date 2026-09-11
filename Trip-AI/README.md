# Trip-AI 旅行规划平台

基于 **LangChain / LangGraph** 多智能体编排的 AI 旅行规划平台，支持用户账户、历史行程管理与行程链接分享。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | FastAPI + SQLAlchemy 2.0 + PostgreSQL(SQLite) + PyJWT + bcrypt |
| Agent 编排 | LangChain + LangGraph（gather 取数 → plan 规划 → enrich 补充 三节点） |
| LLM | DeepSeek（OpenAI 兼容协议，`deepseek-chat`） |
| 外部服务 | 高德地图官方 MCP 服务（本地 stdio 子进程：POI / 天气 / 路线规划）、Unsplash 图片 |
| 前端 | Vue3 + TypeScript + Vite + Ant Design Vue + Pinia + Vue Router |
| 部署 | Docker Compose + Nginx |

## 目录结构

```
Trip-AI/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── agents/          # LangGraph 编排（state/nodes/prompts/graph）
│   │   ├── api/routes/      # auth / trips / share
│   │   ├── core/            # db / security / deps
│   │   ├── models/          # SQLAlchemy 模型（user/trip/share）
│   │   ├── schemas/         # Pydantic schema
│   │   └── services/        # 高德 MCP / 图片服务
│   ├── .env                 # 本地环境变量（含密钥，不提交）
│   └── requirements.txt
├── frontend/                # Vue3 前端
│   ├── src/views/           # Login / Register / Home / Result / MyTrips / ShareView
│   ├── src/components/      # TripMap 高德地图组件
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 本地开发

### 1. 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # 填写真实的 LLM / 高德 / JWT 密钥
python run.py
```

后端默认运行于 http://localhost:8000，交互式文档见 `/docs`。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行于 http://localhost:5173，`/api` 请求会代理到后端 8000 端口。

### 3. 环境变量

后端（`backend/.env`）：

| 变量 | 说明 |
| --- | --- |
| `LLM_API_KEY` | DeepSeek API key |
| `LLM_BASE_URL` | 默认 `https://api.deepseek.com` |
| `AMAP_API_KEY` | 高德地图 Web服务 API key（本地 MCP 服务器以 `AMAP_MAPS_API_KEY` 注入使用） |
| `JWT_SECRET` | JWT 签名密钥（务必修改） |
| `DATABASE_URL` | 默认 `sqlite:///./trip.db` |

前端（`frontend/.env`）：

| 变量 | 说明 |
| --- | --- |
| `VITE_AMAP_WEB_JS_KEY` | 高德地图 Web端 JS API key |

## Docker 部署

```bash
cp .env.example .env             # 填写生产环境密钥
docker compose up -d --build
```

- 前端（Nginx）：http://localhost
- 后端：http://localhost:8000
- 数据库：PostgreSQL（数据持久化于 `pgdata` 卷）

## 核心流程

1. 用户在首页填写目的地、日期、偏好。
2. 后端 `POST /api/trips/generate` 触发 LangGraph 三节点流程：
   - gather 取数节点：确定性调用高德 MCP 工具，收集景点 / 天气 / 酒店真实数据
   - plan 规划节点：LLM 结合真实数据，通过 JSON 模式生成结构化计划
   - enrich 补充节点：按名称回填真实坐标，并规划每日相邻景点的路线
3. 用户可保存行程到个人账户（JWT 鉴权）。
4. 用户可生成分享链接（`secrets.token_urlsafe`），他人通过链接只读查看。

## 安全说明

- `.env` 文件含真实密钥，已加入 `.gitignore`，请勿提交。
- 生产环境务必修改 `JWT_SECRET`，并建议轮换 DeepSeek / 高德 API key。
