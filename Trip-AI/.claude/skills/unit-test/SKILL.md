---
name: unit-test
description: 为 Trip-AI 后端 Python 代码编写并运行 pytest 单元测试，并输出测试报告。当用户要求"写单元测试""跑测试""测试报告""检查某段代码是否正确"时使用。
---

# 单元测试技能

对 Trip-AI 后端代码进行单元测试：分析目标代码 → 编写 pytest 测试 → 执行 → 输出测试报告。

## 执行流程

### 第一步：分析目标
1. 确认用户要测哪个模块/文件；若未指定，先询问，或挑一个纯函数模块（见下方推荐对象）。
2. 阅读目标代码，找出可测单元，优先级从高到低：
   - 纯函数（无数据库、无网络）：如 `app/core/security.py`
   - Pydantic 校验：如 `app/schemas/*.py`
   - 带外部依赖的类：如 `app/services/images.py`（无 key 时返回空列表）
3. 对每个函数，列出要覆盖的用例：正常输入、边界输入、异常输入。

### 第二步：编写测试
1. 在 `backend/tests/` 下新建 `test_<模块名>.py`。
2. 用 pytest 的 `assert` 写用例，函数命名 `test_<描述>`。
3. 覆盖「正常 + 边界 + 异常」三类情况。

### 第三步：执行测试
从 `backend/` 目录运行：

```
.venv/Scripts/python.exe -m pytest -v
```

- 若提示没有 pytest，先执行：`.venv/Scripts/python.exe -m pip install pytest`

### 第四步：输出报告
整理成如下形式，在终端输出：
- 通过 X 条、失败 X 条（总计 X 条）
- 每条失败：文件名 + 行号 + 失败原因（期望值 vs 实际值）
- 若全部通过，明确说「全部通过 ✅」

## 项目专属注意事项（务必遵守）
- 测试文件统一放 `backend/tests/`，命名 `test_*.py`。
- 本项目是**同步** SQLAlchemy + SQLite，纯函数测试**不需要连数据库**，不要写需要启动服务的测试。
- 好上手的测试对象（无外部依赖）：`app/core/security.py`、`app/schemas/*.py`、`app/services/images.py`。
- bcrypt 哈希每次结果随机：断言**行为**（如 `verify_password(...) is True`），**不要**断言具体哈希字符串。
- 必须从 `backend/` 目录运行 pytest（`.env` 和 `app` 包都在那边）。
- 测试代码风格与项目保持一致：中文 docstring、简洁。
