# Trip-AI 旅行规划平台

基于 **LangChain / LangGraph** 多智能体编排的 AI 旅行规划平台，支持用户账户、历史行程管理与行程链接分享。

> 架构设计与技术选型决策详见 [docs/第二版技术方案.md](docs/第二版技术方案.md)。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | FastAPI + SQLAlchemy 2.0 + PostgreSQL(SQLite) + PyJWT + bcrypt |
| 异步任务 | Celery + Redis（行程生成异步化：提交即返回 task_id，前端轮询） |
| 可观测性 | 统一 request_id + loguru 结构化日志 + Langfuse 链路追踪（可选） |
| 错误处理 | 统一业务错误码体系（`{code, message, detail, request_id}` 信封） |
| 测试/CI | pytest + pytest-cov + GitHub Actions（推送即跑测试与覆盖率报告） |
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
│   │   ├── core/            # db / security / deps / celery_app
│   │   ├── models/          # SQLAlchemy 模型（user/trip/share/generation_task）
│   │   ├── schemas/         # Pydantic schema
│   │   ├── tasks/           # Celery 任务（生成任务 / worker 事件循环）
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

> 依赖说明：`requirements.txt` 是 `pip-compile` 生成的锁定文件（精确版本，构建可复现）。升级/新增依赖时，编辑 `requirements.in` 后运行 `pip-compile requirements.in` 重新生成。

### 2. 前端

```bash
cd frontend
npm ci
npm run dev
```

前端默认运行于 http://localhost:5173，`/api` 请求会代理到后端 8000 端口。

> 依赖说明：`npm ci` 严格按 `package-lock.json` 安装（版本完全一致，可复现）。改 `package.json` 后运行 `npm install` 更新锁文件并提交。

### 3. 环境变量

后端（`backend/.env`）：

| 变量 | 说明 |
| --- | --- |
| `LLM_API_KEY` | DeepSeek API key |
| `LLM_BASE_URL` | 默认 `https://api.deepseek.com` |
| `AMAP_API_KEY` | 高德地图 Web服务 API key（本地 MCP 服务器以 `AMAP_MAPS_API_KEY` 注入使用） |
| `JWT_SECRET` | JWT 签名密钥（务必修改） |
| `DATABASE_URL` | 默认 `sqlite:///./trip.db` |
| `REDIS_URL` | Celery broker，默认 `redis://localhost:6379/0` |
| `LOG_LEVEL` | 日志级别，默认 `INFO` |
| `LANGFUSE_ENABLED` | 链路追踪开关，默认 `false`（关闭时无外部依赖） |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Langfuse 云版公钥/私钥（启用时必填） |
| `LANGFUSE_HOST` | Langfuse 地址，默认 `https://cloud.langfuse.com`，可指向自托管 |

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
- Worker：Celery 任务消费进程（`docker compose logs -f worker` 查看日志）
- 数据库：PostgreSQL（数据持久化于 `pgdata` 卷）
- 队列：Redis（Celery broker）

> 行程生成已异步化：后端入队后由 worker 执行，前端轮询任务状态（见下节）。

## 数据库迁移

Schema 变更由 Alembic 管理，迁移脚本位于 `backend/alembic/`，数据库 URL 由 `backend/alembic/env.py` 从 `app/config.py` 读取（可用环境变量 `DATABASE_URL` 覆盖）。

- 后端启动时会自动执行迁移到最新版本（`alembic upgrade head`）。
- 常用命令（在 `backend/` 目录下执行）：
  ```bash
  alembic upgrade head                        # 升级到最新版本
  alembic revision --autogenerate -m "描述"   # 修改模型后生成新迁移
  alembic check                               # 检查模型与迁移是否一致（应无差异）
  ```
- 从旧版（`create_all` 建表、无 `alembic_version` 表）升级：执行一次 `alembic stamp head` 标记当前 schema 为已迁移即可，无需重建数据库。

## 异步任务（Celery）

行程生成是 30–90s 的 LLM + 高德 MCP 长任务，已从请求/响应周期移出：`POST /api/trips/generate` 立即返回 `task_id`（202），由 Celery worker 后台执行，前端轮询 `GET /api/trips/generate/{task_id}` 获取结果。

本地开发需要三个进程（后端目录 `backend/` 下执行）：

```bash
# 1. Redis（broker）
docker run -d -p 6379:6379 redis:7-alpine

# 2. Celery worker
celery -A app.core.celery_app worker --loglevel=info

# 3. FastAPI 后端
python run.py
```

任务状态机：`pending → processing → completed / failed`，结果与错误持久化于 `generation_tasks` 表。worker 采用 `task_acks_late`，进程崩溃后未完成任务会自动重投。

## 核心流程

1. 用户在首页填写目的地、日期、偏好。
2. 后端 `POST /api/trips/generate` 创建生成任务并入队（立即返回 task_id），由 Celery worker 执行 LangGraph 三节点流程：
   - gather 取数节点：确定性调用高德 MCP 工具，收集景点 / 天气 / 酒店真实数据
   - plan 规划节点：LLM 结合真实数据，通过 JSON 模式生成结构化计划
   - enrich 补充节点：按名称回填真实坐标，并规划每日相邻景点的路线
   - 前端轮询任务状态，完成后展示计划（可保存）
3. 用户可保存行程到个人账户（JWT 鉴权）。
4. 用户可生成分享链接（`secrets.token_urlsafe`），他人通过链接只读查看。

## 统一异常处理（业务错误码）

所有错误统一返回 `{code, message, detail, request_id}` 信封，`code` 为分段业务错误码（见 `backend/app/core/errors.py`）：

| 段 | 范围 | 示例 |
| --- | --- | --- |
| 通用 | 1xxxx | `10001` 参数校验失败、`10002` 未登录、`10005` 资源不存在 |
| 用户/认证 | 2xxxx | `20001` 邮箱已注册、`20003` 邮箱或密码错误 |
| 行程 | 3xxxx | `30001` 行程不存在、`30002` 生成任务不存在 |
| 分享 | 4xxxx | `40001` 分享链接不存在、`40002` 已过期 |
| 生成 | 5xxxx | `50001` 行程生成失败 |

- 业务代码统一抛 `BizError(ErrorCode.XXX)`，由全局处理器转成统一结构；校验错误（422）与未捕获异常（500）也走同一信封。
- `request_id` 由请求中间件自动注入，与日志、链路追踪共用，可把一次请求在日志里串起来。
- 前端只需读 `data.message ?? data.detail` 即可拿到可展示文案。

## 可观测性（日志 / 链路追踪）

- **request_id**：`RequestContextMiddleware` 读入或生成 `X-Request-ID` 并回写响应头，写入 contextvar。
- **结构化日志**：loguru 统一格式，每条日志自动带上 `request_id`（无需改动现有 log 语句）。
- **Langfuse 链路追踪**（可选，默认关闭）：设 `LANGFUSE_ENABLED=true` 并填入 key 后，每次行程生成会产出 `trip_generation` 一条 trace，覆盖 gather/plan/enrich 节点与 LLM 调用。
  - 最快路径是 [Langfuse 云版](https://langfuse.com)：填 key 即可，无需部署。
  - 自托管：`docker compose -f docker-compose.langfuse.yml up -d`（6 服务栈，较重），再把 `LANGFUSE_HOST` 指向 `http://localhost:3000`。

## 测试与 CI

- 测试位于 `backend/tests/`，覆盖：错误码信封、认证路由、行程归属隔离（越权返回 404）、分享链接 404/410、`_parse_plan_json` 解析、以及一条**真实 LangGraph 链集成测试**（mock LLM/MCP/图片，不触网，验证取数 → 规划 → 坐标回填 → 路线生成全流程）。
- **离线评测集** `backend/tests/test_eval_set.py`：参数化多个城市场景（北京/上海/杭州/成都 × 公交/自驾/步行），回归断言「JSON 合法、天数正确、景点不编造、坐标已回填、路线已生成」。改 prompt（`app/agents/prompts.py` 的 `PROMPT_VERSION`）或编排逻辑后，跑一遍即可判断有没有改坏。
- 本地运行（`backend/` 下）：

  ```bash
  pip install -r requirements-dev.txt
  pytest -v --cov=app --cov-report=term-missing
  ```

- CI：`.github/workflows/backend-ci.yml` 在 push / PR 到 `master`/`main`/`develop` 时跑 Python 3.11 测试并输出覆盖率报告（只报告、不设门槛）。

## 安全说明

- `.env` 文件修改为自己的真实密钥。
- 生产环境务必修改 `JWT_SECRET`，并建议轮换 DeepSeek / 高德 API key。
- 数据库密码通过 `POSTGRES_PASSWORD` 环境变量注入（不在编排文件里写死），生产部署前在 `.env` 设一个强密码。
