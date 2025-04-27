from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from libs.tarkov_api import TarkovMarketAPI
from libs.config import Config, load_config

def setup_handlers(application):
    config = load_config()
    api = TarkovMarketAPI(config)
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "欢迎使用Tarkov Market查询机器人！\n"
            "请输入物品名称查询价格信息\n"
            "在群组中使用/price [物品名]查询"
        )
    
    async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("请指定物品名称，例如: /price 比特币")
            return
            
        item_name = " ".join(context.args)
        await search_item(update, context, item_name)
    
    async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item_name=None):
        if item_name is None:
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
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_item))