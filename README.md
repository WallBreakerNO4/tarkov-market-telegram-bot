# Tarkov Market Telegram Bot

一个查询Escape from Tarkov物品价格的Telegram机器人

## 环境要求
- Python 3.8+
- Telegram Bot Token
- tarkov.dev API（免费，无需密钥）

## 安装步骤

1. 复制环境变量模板
```bash
cp .env.example .env
```

2. 编辑.env文件，填写你的配置
```
TELEGRAM_BOT_TOKEN=你的Telegram机器人令牌
# 已迁移到 tarkov.dev（免费），无需 API Token；保留兼容旧配置
TARKOV_MARKET_API_TOKEN=
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行机器人
```bash
python bot.py
```

## 功能说明
- 输入物品名称查询当前价格
- 显示24小时和7天平均价格
- 显示商人回收价格

## API使用限制
请遵守[tarkov.dev](https://tarkov.dev/) 的相关使用条款与限制
