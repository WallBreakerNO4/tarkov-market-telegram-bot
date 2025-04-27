import os
import asyncio
import logging
from telegram.ext import ApplicationBuilder
from libs.config import load_config

def main():
    # 配置日志输出到终端
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    # 设置httpx日志级别为WARNING，减少网络请求日志
    logging.getLogger("httpx").setLevel(logging.WARNING)
    config = load_config()
    application = ApplicationBuilder().token(config.telegram_token).build()
    
    # 注册消息处理器
    from libs.handlers import setup_handlers
    setup_handlers(application)
    
    application.run_polling()

if __name__ == "__main__":
    main()