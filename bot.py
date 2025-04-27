import os
import asyncio
from telegram.ext import ApplicationBuilder
from libs.config import load_config

def main():
    config = load_config()
    application = ApplicationBuilder().token(config.telegram_token).build()
    
    # 注册消息处理器
    from libs.handlers import setup_handlers
    setup_handlers(application)
    
    application.run_polling()

if __name__ == "__main__":
    main()