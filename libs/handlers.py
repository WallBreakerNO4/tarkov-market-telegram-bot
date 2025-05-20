import logging
from telegram import Update, MessageEntity # 确保 MessageEntity 已导入
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from libs.tarkov_api import TarkovMarketAPI
from libs.config import load_config # config 类不再需要单独导入

logger = logging.getLogger(__name__)

# 1. 创建通用的搜索与回复辅助函数
async def _search_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, item_name: str, tarkov_api: TarkovMarketAPI):
    logger.info(f"用户查询: {item_name} (用户ID: {update.effective_user.id}, 聊天ID: {update.effective_chat.id})")
    
    items = tarkov_api.search_item(item_name)
    
    if not items:
        await update.message.reply_text("未找到该物品。")
        return
        
    # 假设总是取API返回的第一个结果
    item = items[0] 
    
    # 从item字典中安全地获取信息
    item_name_display = item.get('name', item_name) # 如果API没返回name，就用用户输入的
    price = item.get('price', 'N/A')
    avg24h_price = item.get('avg24hPrice', 'N/A')
    avg7days_price = item.get('avg7daysPrice', 'N/A')
    trader_name = item.get('traderName', 'N/A')
    trader_price = item.get('traderPrice', 'N/A')

    message_text = (
        f"物品: {item_name_display}\n"
        f"当前价格: {price} ₽\n"
        f"24小时均价: {avg24h_price} ₽\n"
        f"7天均价: {avg7days_price} ₽\n"
        f"商人: {trader_name} ({trader_price} ₽)"
    )
    
    await update.message.reply_text(message_text) # 默认以纯文本发送

def setup_handlers(application):
    config = load_config()
    api = TarkovMarketAPI(config) # API实例在设置处理器时创建一次

    # 2. 更新 /start 命令的帮助信息
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot_username = context.bot.username # 在函数内部获取机器人用户名
        await update.message.reply_text(
            "欢迎使用塔科夫市场查询机器人！\n\n"
            f"🔹 **私聊我**: 直接发送物品名称即可查询价格。\n"
            f"   例如: `显卡`\n\n"
            f"🔹 **在群组中**: \n"
            f"   - 使用命令: `/price [物品名]`\n"
            f"     例如: `/price 军用电缆`\n"
            f"   - 或者直接艾特我: `@{bot_username} [物品名]`\n"
            f"     例如: `@{bot_username} 应急水过滤器`"
        )

    # 3. 修改 /price 命令处理器
    async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("请提供物品名称。用法: `/price [物品名]`")
            return
        item_name = " ".join(context.args)
        await _search_and_reply(update, context, item_name, api)

    # 4. 添加处理 @机器人名称 <物品名> 的新处理器
    async def mention_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message or not message.text: # 确保消息和文本存在
            return

        # 此处理器仅用于群组和超级群组
        if not (update.effective_chat.type == "group" or update.effective_chat.type == "supergroup"):
            return

        bot_username = context.bot.username
        mention_string = f"@{bot_username}"
        
        item_name_from_mention = None

        # 检查消息实体，确保第一个实体是提及机器人
        if message.entities:
            for entity in message.entities:
                if entity.type == MessageEntity.MENTION and entity.offset == 0: # 提及在消息开头
                    mentioned_text = message.text[entity.offset : entity.offset + entity.length]
                    if mentioned_text == mention_string: # 确认是提及机器人本身
                        item_name_from_mention = message.text[entity.length:].strip() # 提取物品名
                        break 
        
        if item_name_from_mention: # 如果成功从提及中提取到物品名
            await _search_and_reply(update, context, item_name_from_mention, api)
        elif message.text.startswith(mention_string) and not item_name_from_mention:
            # 如果是 @机器人 但后面没有物品名
            await message.reply_text(f"请在 {mention_string} 后指定物品名称，例如: {mention_string} 比特币")

    # 5. 修改原有的文本消息处理器，使其仅在私聊中生效
    async def private_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 仅在私聊中处理，并且消息不是命令
        if update.effective_chat.type == "private" and \
           update.message and update.message.text and \
           not update.message.text.startswith('/'):
            item_name = update.message.text
            await _search_and_reply(update, context, item_name, api)

    # 注册所有处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price_command))
    
    # 群聊中 @机器人名称 的处理器
    # 过滤器: 是文本消息, 不是命令, 在群组或超级群组中, 并且包含提及实体
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP) & filters.Entity(MessageEntity.MENTION),
        mention_search
    ))
    
    # 私聊中的文本处理器
    # 过滤器: 是文本消息, 不是命令, 在私聊中
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        private_text_search
    ))