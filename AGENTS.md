# 仓库代理指南（tarkov-market-telegram-bot）

本文件提供给在此仓库内工作的各类 agent（自动化编码代理/代码审阅代理/脚本代理）。目标是：不猜、不发明；命令必须可运行；缺失的工具链要明确写“未配置”。

协作约定：
- 交流语言：中文
- 如需写 git 提交信息：中文

## 项目是什么

- 作用：Telegram 机器人，查询《逃离塔科夫》物品价格（当前走 `tarkov.dev` GraphQL）
- 入口：`bot.py`
- 主要模块：
  - `libs/config.py`：环境变量加载与校验（`Config` dataclass）
  - `libs/handlers.py`：Telegram 异步 handlers 与消息路由
  - `libs/tarkov_api.py`：GraphQL 客户端（同步 `requests`）

## 编辑器/代理规则（Cursor / Copilot）

- 未发现 Cursor 规则：仓库内不存在 `.cursor/rules/` 与 `.cursorrules`
- 未发现 Copilot 规则：仓库内不存在 `.github/copilot-instructions.md`

## 运行与依赖

### Python

- 以仓库为准：Python 3.14（`.python-version`、`pyproject.toml`）
- 注意：`README.md` 的 “Python 3.8+” 已过时

### 环境变量

1. `cp .env.example .env`
2. 必填：`TELEGRAM_BOT_TOKEN`
3. 可选：
   - `TARKOV_MARKET_API_TOKEN`：迁移到 `tarkov.dev` 后可为空（保留兼容旧配置）
   - `END_POINT_TYPE`：`pvp`（默认）或 `pve`

### 安装依赖

仓库有 `pyproject.toml` + `uv.lock`，但根目录缺 `requirements.txt`（因此 `README.md` 的 `pip install -r requirements.txt` 目前不可用）。

- 推荐（uv）：`uv sync`
- 兜底（pip，按 `pyproject.toml` 依赖列表安装）：
  - `python -m pip install "python-dotenv>=1.2.1" "python-telegram-bot[socks]>=22.6" "requests>=2.32.5"`

### 启动

- `python bot.py`

## Docker / Compose

- `docker build -t tarkov-telegram-bot .`
- `docker run --rm --name tarkov-telegram-bot --env-file .env tarkov-telegram-bot`
- `docker compose up -d --build`

注意：`Dockerfile` 依赖 `requirements.txt`，但仓库当前没有该文件；现状下 Docker 构建会失败。

## 构建 / Lint / 格式化 / 类型检查 / 测试

- build：未配置（无 Makefile/脚本）
- lint/format：未配置（未发现 Ruff/Black/isort/flake8 配置）
- typecheck：未配置（未发现 mypy/pyright 配置）
- test：未配置（无 `tests/`、无 pytest 配置）
- 运行单个测试：不适用

将来若引入 pytest，约定：
- 跑全部：`pytest`
- 跑单文件：`pytest tests/test_x.py`
- 跑单测例：`pytest tests/test_x.py::test_name`

## 代码风格与约定（跟随现有代码）

### Imports

- 分组并以空行隔开：标准库 / 第三方 / 本地（`libs.*`）
- 禁止 `import *`

示例：
```python
import logging

from telegram import Update
from telegram.ext import ContextTypes

from libs.config import load_config
```

### Formatting

- 4 空格缩进
- 多行文本优先括号拼接 + 显式 `\n`，避免三引号导致缩进/空格难控
- 复杂条件优先换行拆分（参考 `libs/handlers.py` 的 entity 解析）

### Naming

- 类：PascalCase（`Config`、`TarkovMarketAPI`）
- 函数/变量：snake_case
- 常量：UPPER_CASE
- 内部辅助函数：前导下划线（如 `_search_and_reply`）

### Types

- 轻量标注即可：配置用 `@dataclass`；handlers/API public 方法尽量写参数与返回值
- 当前未启用类型检查器：不要为“类型好看”引入大段样板

### Async（python-telegram-bot v22+）

- handler 必须 `async def` 并 `await` Telegram API（`reply_text` 等）
- handler 保持“薄”，业务/HTTP 放 `libs/`
- 避免新增阻塞 I/O；现有 `libs/tarkov_api.py` 使用同步 `requests` 会阻塞事件循环
- 如需调用同步函数，放线程池：

```python
import asyncio


async def handler(update, context):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, sync_call)
```

参考：
- https://docs.python-telegram-bot.org/en/latest/telegram.ext.applicationbuilder.html
- https://github.com/python-telegram-bot/python-telegram-bot/wiki/Concurrency

### Error handling

- 配置缺失必填 env：抛 `ValueError`（`libs/config.py`）
- HTTP 调用：捕获 `requests.exceptions.RequestException` 与 JSON 解析异常，失败返回 `None`（`libs/tarkov_api.py`）
- 禁止空 `except`；禁止吞异常不记录
- handlers 中先判空：`update.effective_message`/`message.text`

### Logging

- 模块内：`logger = logging.getLogger(__name__)`
- 入口：`bot.py` 统一 `logging.basicConfig(...)`，并降低 `httpx` 噪音
- 新增代码优先用 `logging`，不要引入新的 `print`（`libs/tarkov_api.py` 的 `print` 属历史不一致点）
- 不记录 secrets（token/key/完整 `.env`）

### 用户文案

- 对用户回复以中文为主；保持用词与格式一致
- 默认纯文本 `reply_text`；如切换 Markdown/HTML，注意转义与实体

## 配置与密钥（Secrets）

- `.env` 已在 `.gitignore` 忽略：不要提交
- 新增配置项时同步更新 `.env.example`
- 禁止在日志/异常中输出 `TELEGRAM_BOT_TOKEN`、`TARKOV_MARKET_API_TOKEN`

## 常见改动入口

- 新增命令/交互：改 `libs/handlers.py`，并在 `setup_handlers(...)` 注册；优先复用 `_search_and_reply`
- 修改 API：优先局部改 `libs/tarkov_api.py`；handler 只做参数解析与输出格式

## 已知不一致（写代码时要注意）

- `README.md` 提到 `requirements.txt`，但仓库当前缺少该文件
- `Dockerfile` 依赖 `requirements.txt`，现状下 Docker 构建会失败
- `libs/tarkov_api.py` 使用同步 `requests` + `print`，与 handlers 里的 `logging` 风格不一致

## 不确定时

- 以 `bot.py` 与 `libs/` 现有写法为准；改动尽量小、尽量局部、可读性优先
