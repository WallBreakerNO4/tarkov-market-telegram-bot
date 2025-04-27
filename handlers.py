from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from tarkov_api import TarkovMarketAPI
from config import Config, load_config

def setup_handlers(application):
    config = load_config()
    api = TarkovMarketAPI(config)
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "欢迎使用Tarkov Market查询机器人！\n"
            "请输入物品名称查询价格信息"
        )
    
    async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
        item_name = update.message.text
        items = api.search_item(item_name)
        
        if not items:
            await update.message.reply_text("未找到该物品")
            return
            
        item = items[0]
        message = (
            f"物品: {item['name']}\n"
            f"当前价格: {item['price']} ₽\n"
            f"24小时均价: {item['avg24hPrice']} ₽\n"
            f"7天均价: {item['avg7daysPrice']} ₽\n"
            f"商人: {item['traderName']} ({item['traderPrice']} ₽)"
        )
        await update.message.reply_text(message)
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_item))