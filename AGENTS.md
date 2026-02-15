# 仓库代理指南（tarkov-market-telegram-bot）

本文件提供给在此仓库内工作的各类 agent（自动化编码代理/代码审阅代理/脚本代理）。目标是：不猜、不发明，按仓库现状给出可执行命令与明确的代码约定。

## 项目是什么

- 作用：Telegram 机器人，调用 Tarkov Market API 查询《逃离塔科夫》物品价格
- 入口：`bot.py`
- 主要模块：
  - `libs/config.py`：环境变量加载与校验（`Config` dataclass）
  - `libs/handlers.py`：Telegram 异步 handlers 与消息路由
  - `libs/tarkov_api.py`：Tarkov Market API 的 HTTP 客户端封装

## 编辑器/代理规则（Cursor / Copilot）

- 未发现 Cursor 规则：仓库内不存在 `.cursor/rules/` 与 `.cursorrules`
- 未发现 Copilot 规则：仓库内不存在 `.github/copilot-instructions.md`
- 本仓库仅此一份指南：`AGENTS.md`

补充（适用于本仓库的 agent 协作约定）：
- 交流语言：中文
- 如需写 git 提交信息：中文

## 快速开始（本地）

1. 准备环境变量文件：
   - `cp .env.example .env`
   - 必填（见 `.env.example`、`libs/config.py`）：
     - `TELEGRAM_BOT_TOKEN`
     - `TARKOV_MARKET_API_TOKEN`
   - 可选：
     - `END_POINT_TYPE`：`pvp`（默认）或 `pve`

2. 安装依赖：
   - `pip install -r requirements.txt`

3. 运行机器人：
   - `python bot.py`

命令来源：`README.md`

## Docker / Compose

- 构建镜像：`docker build -t tarkov-telegram-bot .`
- 运行（读取 `.env`）：`docker run --rm --name tarkov-telegram-bot --env-file .env tarkov-telegram-bot`
- Compose（后台运行并构建）：`docker compose up -d --build`
  - Compose 会挂载 `./.env:/app/.env`（见 `docker-compose.yml`）

来源：`Dockerfile`、`docker-compose.yml`

## 构建 / Lint / 格式化 / 类型检查 / 测试

必须以仓库实际为准，不要发明命令：

- 构建（build）：未配置（无 Makefile、无脚本系统）
- Lint：未配置（未发现 Ruff/Black/isort/flake8 等配置文件）
- 格式化：未配置
- 类型检查：未配置（未发现 mypy/pyright 配置）
- 测试：未配置（无 `tests/` 目录、无 pytest 配置）
- 运行单个测试：不适用（在补充测试体系之前无法运行）

如果你引入上述工具链，请在本文件补充“确切可运行”的命令（含单测运行方式）。

## 代码风格与约定（跟随现有代码）

### 导入（imports）

- 分组并以空行隔开：
  1) 标准库
  2) 第三方
  3) 本地模块（`libs.*`）
- 不使用 `import *`

示例：`bot.py`、`libs/handlers.py`

### 格式（formatting）

- 4 空格缩进
- 长字符串使用括号拼接，行内通过显式 `\n` 组织多行文本
- 以可读性优先，避免极长行

示例：`libs/handlers.py`

### 命名（naming）

- 类：PascalCase（如 `Config`、`TarkovMarketAPI`）
- 函数/变量：snake_case（如 `load_config`、`search_item`）
- 常量：UPPER_CASE（如 `BASE_URL_PVP`）
- 内部辅助函数：前导下划线（如 `_search_and_reply`）

### 类型（types）

- 倾向“轻量”类型标注：
  - 配置对象用 dataclass
  - 核心函数/接口参数与返回值写注解（尤其是 handlers）
- 当前仓库未启用类型检查器，不要为了“过度类型化”引入大量样板

示例：`libs/config.py`、`libs/handlers.py`、`libs/tarkov_api.py`

### 异步与 Telegram handlers

- handler 使用 `async def`，并 `await` Telegram API（`reply_text` 等）
- 按聊天类型路由：
  - 私聊：直接发物品名文本查询
  - 群聊：使用 `/price` 或 @机器人 + 物品名

示例：`libs/handlers.py`

注意：`libs/tarkov_api.py` 通过同步 `requests` 发 HTTP；在 handler 内尽量避免新增额外阻塞工作。

### 错误处理（error handling）

- 配置加载：缺失必要环境变量应抛出清晰异常（当前为 `ValueError`，见 `libs/config.py`）
- HTTP 调用：捕获 `requests.exceptions.RequestException`，失败时输出错误并返回 `None`（见 `libs/tarkov_api.py`）
- 禁止空 `except` / 静默吞异常

### 日志（logging）

- 模块内：`logger = logging.getLogger(__name__)`
- 入口统一配置：`bot.py` 中 `logging.basicConfig(...)`
- 日志记录用户行为用于追踪，但不要记录 token / key 等敏感信息

示例：`bot.py`、`libs/handlers.py`

### 用户文案 / i18n

- 当前回复与帮助信息以中文为主；新增用户可见文案保持中文一致性
- 默认用纯文本 `reply_text`；如需 Markdown/HTML，需谨慎处理转义与显示效果

## 配置与密钥（Secrets）

- 不要提交 `.env`（已在 `.gitignore` 中忽略）
- 新增配置项时同步更新 `.env.example`
- 禁止在日志/错误信息中输出 `TELEGRAM_BOT_TOKEN`、`TARKOV_MARKET_API_TOKEN`

## 常见改动入口

- 新增命令：
  - 在 `libs/handlers.py` 添加 async handler
  - 在 `setup_handlers(...)` 中注册 `application.add_handler(...)`
  - 优先复用 `_search_and_reply` 这类抽象，避免重复拼装回复

- 修改 API 行为：
  - 优先局部修改 `libs/tarkov_api.py`
  - handler 尽量保持“薄”，只做参数解析与回复

## 不确定时

- 以 `bot.py` 与 `libs/` 现有写法为准
- 改动尽量小、尽量局部、可读性优先
