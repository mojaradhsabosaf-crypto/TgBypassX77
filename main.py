# main.py
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from config import BOT_TOKEN
from database import Database
from handlers import (
    start, daily, balance, x11, refer, bypass, redeem_command,
    handle_redeem_code, cancel, button_callback, handle_message,
    WAITING_FOR_NUMBER, WAITING_FOR_USERNAME, WAITING_FOR_REDEEM_CODE
)
from anti_spam import anti_spam

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Rocket system (bomber) commands
async def bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bomb command"""
    if not context.args:
        await update.message.reply_text(
            "<blockquote>🚀 <b>ROCKET COMMAND</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Usage: <code>/bomb +919876543210</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <i>Enter target number to launch rockets</i></blockquote>",
            parse_mode='HTML'
        )
        return
    
    number = context.args[0]
    user_id = update.effective_user.id
    
    # Check bypass or credits
    has_bypass = db.has_bypass(user_id)
    
    if not has_bypass:
        if not db.deduct_credits(user_id, 2):
            await update.message.reply_text(
                "<blockquote>❌ <b>INSUFFICIENT CREDITS</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Rockets cost 2 credits per launch!\n\n"
                f"💰 Your balance: {db.get_credits(user_id)}\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "💡 <i>Use /daily to get free credits</i></blockquote>",
                parse_mode='HTML'
            )
            return
    
    await update.message.reply_text(
        f"<blockquote>🚀 <b>ROCKETS LAUNCHED!</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 <b>Target:</b> <code>{number}</code>\n"
        f"💣 <b>Status:</b> Sending 50 rockets...\n"
        f"⏱️ <b>ETA:</b> 30 seconds\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ <i>Use /stopbomb to stop all rockets</i></blockquote>",
        parse_mode='HTML'
    )
    
    # Log the action
    db.log_search(user_id, "rocket", number)

async def stopbomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop bomb command"""
    await update.message.reply_text(
        "<blockquote>🛑 <b>ROCKETS STOPPED</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ All active rockets have been stopped.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💫 <i>System is now idle</i></blockquote>",
        parse_mode='HTML'
    )

async def ff_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Free Fire info command"""
    if not context.args:
        await update.message.reply_text(
            "<blockquote>🎮 <b>FREE FIRE INFO</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Usage: <code>/ffinfo 2819649271</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <i>Enter Free Fire UID to get info</i></blockquote>",
            parse_mode='HTML'
        )
        return
    
    uid = context.args[0]
    user_id = update.effective_user.id
    
    # Check bypass or credits
    has_bypass = db.has_bypass(user_id)
    
    if not has_bypass:
        if not db.deduct_credits(user_id, 1):
            await update.message.reply_text(
                "<blockquote>❌ <b>INSUFFICIENT CREDITS</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "FF Info costs 1 credit!\n\n"
                f"💰 Your balance: {db.get_credits(user_id)}\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "💡 <i>Use /daily to get free credits</i></blockquote>",
                parse_mode='HTML'
            )
            return
    
    # Mock FF info - replace with real API
    db.log_search(user_id, "freefire", uid)
    
    await update.message.reply_text(
        f"<blockquote>🎮 <b>FREE FIRE INFORMATION</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <b>UID:</b> <code>{uid}</code>\n"
        f"👤 <b>Nickname:</b> Player_{uid[-4:]}\n"
        f"⭐ <b>Level:</b> 65\n"
        f"🏆 <b>Rank:</b> Heroic\n"
        f"❤️ <b>Likes:</b> 1,240\n"
        f"🌍 <b>Region:</b> Asia\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💫 <i>Data fetched from Free Fire API</i></blockquote>",
        parse_mode='HTML'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "<blockquote>⚠️ <b>ERROR OCCURRED</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "An unexpected error occurred.\n"
            "Please try again later or contact support.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👑 <b>Support:</b> @XITDARKX77</blockquote>",
            parse_mode='HTML'
        )

async def group_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group messages with spam protection"""
    if not update.message or not update.message.text:
        return
    
    result = await anti_spam.handle_group_message(update, context)
    
    if result == "phone":
        await update.message.reply_text(
            "<blockquote>📞 <b>PHONE NUMBER DETECTED</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Use this in private chat with @TheDarkX77_bot\n"
            "to get full information!\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <i>Send the number to our bot privately</i></blockquote>",
            parse_mode='HTML'
        )
    elif result == "username":
        await update.message.reply_text(
            "<blockquote>👤 <b>USERNAME DETECTED</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Use this in private chat with @TheDarkX77_bot\n"
            "to get full user information!\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <i>Send the username to our bot privately</i></blockquote>",
            parse_mode='HTML'
        )
    elif result is False:
        # Message was spam and was handled
        pass

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for redeem
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('redeem', redeem_command),
            CallbackQueryHandler(button_callback, pattern='menu_redeem')
        ],
        states={
            WAITING_FOR_REDEEM_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_redeem_code)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(cancel, pattern='cancel')
        ]
    )
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('daily', daily))
    application.add_handler(CommandHandler('balance', balance))
    application.add_handler(CommandHandler('x11', x11))
    application.add_handler(CommandHandler('refer', refer))
    application.add_handler(CommandHandler('bypass', bypass))
    application.add_handler(CommandHandler('bomb', bomb))
    application.add_handler(CommandHandler('stopbomb', stopbomb))
    application.add_handler(CommandHandler('ffinfo', ff_info))
    application.add_handler(conv_handler)
    
    # Callback handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Group handler for auto-reply in groups
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
        group_handler
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 Bot is starting...")
    print(f"✅ Bot @TheDarkX77_bot is now running!")
    print(f"👑 Developer: @XITDARKX77")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()