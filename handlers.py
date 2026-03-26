# handlers.py
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext
from database import Database
from keyboards import get_main_menu, get_second_page, get_back_menu, get_cancel_button
from utils import search_by_phone, search_by_username, x11_multiplier
from anti_spam import anti_spam
from bypass import bypass_system

db = Database()

# Conversation states
WAITING_FOR_NUMBER = 1
WAITING_FOR_USERNAME = 2
WAITING_FOR_FF_UID = 3
WAITING_FOR_REDEEM_CODE = 4

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Check if user exists
    existing_user = db.get_user(user.id)
    
    # Check for referral
    referred_by = None
    if context.args and len(context.args) > 0:
        ref_code = context.args[0]
        # Find user by referral code
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (ref_code,))
            result = cursor.fetchone()
            if result and result['user_id'] != user.id:
                referred_by = result['user_id']
    
    if not existing_user:
        db.create_user(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name,
            referred_by
        )
    
    # Get user credits
    credits = db.get_credits(user.id)
    
    # Welcome message with quote formatting (not code block)
    welcome_text = (
        f"<blockquote>✨ <b>WELCOME TO THE DARK X77 BOT</b> ✨\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>User:</b> {user.first_name}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Credits:</b> {credits}\n"
        f"⭐ <b>Status:</b> {'BYPASS ACTIVE' if db.has_bypass(user.id) else 'NORMAL'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 <b>Available Features:</b>\n"
        f"   📞 Phone Number Lookup\n"
        f"   👤 Telegram User Info\n"
        f"   🎮 Free Fire Details\n"
        f"   🚀 Rocket System\n"
        f"   ⚡ X11 Multiplier\n"
        f"   🛡️ Bypass Mode\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>Quick Commands:</b>\n"
        f"   /daily - Claim free credits\n"
        f"   /balance - Check credits\n"
        f"   /bypass - Activate bypass\n"
        f"   /refer - Get referral link\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 <b>Links:</b>\n"
        f"   🌐 <a href='{__import__('config').WEBSITE_URL}'>Website</a>\n"
        f"   👥 <a href='{__import__('config').GROUP_URL}'>Group</a>\n"
        f"   👑 Developer: {__import__('config').DEV_USERNAME}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💫 <i>Use the buttons below to get started!</i></blockquote>"
    )
    
    # Try to send video first, if fails send only text
    try:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=__import__('config').WELCOME_VIDEO,
            caption=welcome_text,
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
    except:
        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle daily reward"""
    user_id = update.effective_user.id
    
    if db.can_claim_daily(user_id):
        db.add_credits(user_id, 2)
        db.update_daily(user_id)
        new_credits = db.get_credits(user_id)
        
        await update.message.reply_text(
            f"<blockquote>🎁 <b>DAILY REWARD CLAIMED!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Reward:</b> +2 Credits\n"
            f"📊 <b>New Balance:</b> {new_credits} Credits\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <i>Come back tomorrow for more!</i></blockquote>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "<blockquote>⚠️ <b>Already Claimed!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "You've already claimed your daily reward today.\n"
            "Come back tomorrow for more credits!</blockquote>",
            parse_mode='HTML'
        )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user balance"""
    user_id = update.effective_user.id
    credits = db.get_credits(user_id)
    user = db.get_user(user_id)
    
    await update.message.reply_text(
        f"<blockquote>💰 <b>CREDITS BALANCE</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>User:</b> {update.effective_user.first_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"💎 <b>Credits:</b> {credits}\n"
        f"📊 <b>Total Searches:</b> {user['total_searches'] if user else 0}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ <b>Bypass Status:</b> {'✅ ACTIVE' if db.has_bypass(user_id) else '❌ INACTIVE'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 <i>Use /daily to get free credits!</i></blockquote>",
        parse_mode='HTML'
    )

async def x11(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """X11 Multiplier command"""
    user_id = update.effective_user.id
    result = await x11_multiplier(user_id)
    await update.message.reply_text(result, parse_mode='Markdown')

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get referral link"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        referral_link = f"https://t.me/{__import__('config').BOT_TOKEN.split(':')[0]}?start={user['referral_code']}"
        
        await update.message.reply_text(
            f"<blockquote>👥 <b>REFERRAL SYSTEM</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 <b>Your Referral Link:</b>\n"
            f"<code>{referral_link}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎁 <b>Rewards:</b>\n"
            f"   • You get +5 credits per referral\n"
            f"   • Your friend gets +10 credits\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 <b>Stats:</b>\n"
            f"   • Total Referrals: ?\n"
            f"   • Credits Earned: ?\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💫 <i>Share your link and earn credits!</i></blockquote>",
            parse_mode='HTML'
        )

async def bypass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate bypass mode"""
    user_id = update.effective_user.id
    
    # Check if bypass already active
    if db.has_bypass(user_id):
        await update.message.reply_text(
            "<blockquote>🛡️ <b>BYPASS ALREADY ACTIVE</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Your bypass mode is currently active.\n\n"
            "🔓 <b>Benefits:</b>\n"
            "   • No spam restrictions\n"
            "   • Unlimited searches\n"
            "   • Priority access\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <i>Enjoy unlimited access!</i></blockquote>",
            parse_mode='HTML'
        )
        return
    
    result = await bypass_system.request_bypass(user_id, context)
    
    if result['success']:
        await update.message.reply_text(result['message'], parse_mode='Markdown')
    else:
        await update.message.reply_text(result['message'], parse_mode='Markdown')

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start redeem conversation"""
    await update.message.reply_text(
        "<blockquote>🎟️ <b>REDEEM CODE</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please enter your redeem code:\n\n"
        "<code>EXAMPLE123</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ <i>Enter your code now or press Cancel</i></blockquote>",
        parse_mode='HTML',
        reply_markup=get_cancel_button()
    )
    return WAITING_FOR_REDEEM_CODE

async def handle_redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle redeem code input"""
    code = update.message.text.strip().upper()
    user_id = update.effective_user.id
    
    credits = db.use_redeem_code(code, user_id)
    
    if credits:
        db.add_credits(user_id, credits)
        new_credits = db.get_credits(user_id)
        
        await update.message.reply_text(
            f"<blockquote>✅ <b>CODE REDEEMED SUCCESSFULLY!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎁 <b>Reward:</b> +{credits} Credits\n"
            f"💰 <b>New Balance:</b> {new_credits} Credits\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <i>Thank you for using The Dark X77 Bot!</i></blockquote>",
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text(
            "<blockquote>❌ <b>INVALID OR USED CODE</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "The code you entered is invalid or has already been used.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 <i>Check with the developer for valid codes!</i></blockquote>",
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.callback_query.message.edit_text(
        "<blockquote>❌ <b>CANCELLED</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Operation cancelled successfully!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💫 <i>Use /start to return to main menu</i></blockquote>",
        parse_mode='HTML',
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "main_menu":
        await query.message.edit_caption(
            caption=f"<blockquote>✨ <b>WELCOME BACK!</b> ✨\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💰 <b>Credits:</b> {db.get_credits(user_id)}\n"
                    f"🛡️ <b>Bypass:</b> {'✅' if db.has_bypass(user_id) else '❌'}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💫 <i>Choose an option below:</i></blockquote>",
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
    
    elif data == "next_page":
        await query.message.edit_caption(
            caption=f"<blockquote>📋 <b>PAGE 2 - MORE FEATURES</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💰 <b>Credits:</b> {db.get_credits(user_id)}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💫 <i>Additional tools available:</i></blockquote>",
            parse_mode='HTML',
            reply_markup=get_second_page()
        )
    
    elif data == "prev_page":
        await query.message.edit_caption(
            caption=f"<blockquote>✨ <b>MAIN MENU</b> ✨\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💰 <b>Credits:</b> {db.get_credits(user_id)}\n"
                    f"🛡️ <b>Bypass:</b> {'✅' if db.has_bypass(user_id) else '❌'}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💫 <i>Choose an option below:</i></blockquote>",
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
    
    elif data == "menu_number":
        await query.message.reply_text(
            "<blockquote>📞 <b>NUMBER INFO</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Please send the phone number you want to lookup:\n\n"
            "<code>+919876543210</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ <i>This will cost 1 credit (bypass users free)</i></blockquote>",
            parse_mode='HTML',
            reply_markup=get_cancel_button()
        )
        return WAITING_FOR_NUMBER
    
    elif data == "menu_username":
        await query.message.reply_text(
            "<blockquote>👤 <b>USERNAME INFO</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Please send the username you want to lookup:\n\n"
            "<code>@username</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ <i>This will cost 1 credit (bypass users free)</i></blockquote>",
            parse_mode='HTML',
            reply_markup=get_cancel_button()
        )
        return WAITING_FOR_USERNAME
    
    elif data == "menu_daily":
        if db.can_claim_daily(user_id):
            db.add_credits(user_id, 2)
            db.update_daily(user_id)
            new_credits = db.get_credits(user_id)
            await query.message.reply_text(
                f"<blockquote>🎁 <b>DAILY REWARD CLAIMED!</b>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💰 <b>Reward:</b> +2 Credits\n"
                f"📊 <b>New Balance:</b> {new_credits} Credits\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✨ <i>Come back tomorrow for more!</i></blockquote>",
                parse_mode='HTML'
            )
        else:
            await query.message.reply_text(
                "<blockquote>⚠️ <b>Already Claimed!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "You've already claimed your daily reward today.\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "💫 <i>Come back tomorrow for more!</i></blockquote>",
                parse_mode='HTML'
            )
    
    elif data == "menu_x11":
        result = await x11_multiplier(user_id)
        await query.message.reply_text(result, parse_mode='Markdown')
    
    elif data == "menu_rocket":
        await query.message.reply_text(
            "<blockquote>🚀 <b>ROCKET SYSTEM</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ <b>Available Rockets:</b>\n\n"
            "   🔥 <code>/bomb +919876543210</code>\n"
            "   💣 <code>/rocket +919876543210</code>\n"
            "   🎯 <code>/strike +919876543210</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ <b>Commands:</b>\n"
            "   /stopbomb - Stop active bombing\n"
            "   /status - Check rocket status\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <i>Use with caution!</i></blockquote>",
            parse_mode='HTML'
        )
    
    elif data == "menu_balance":
        credits = db.get_credits(user_id)
        user = db.get_user(user_id)
        await query.message.reply_text(
            f"<blockquote>💰 <b>CREDITS BALANCE</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💎 <b>Credits:</b> {credits}\n"
            f"📊 <b>Searches:</b> {user['total_searches'] if user else 0}\n"
            f"🛡️ <b>Bypass:</b> {'✅' if db.has_bypass(user_id) else '❌'}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 <i>Use /daily for free credits!</i></blockquote>",
            parse_mode='HTML'
        )
    
    elif data == "menu_redeem":
        await redeem_command(update, context)
        return WAITING_FOR_REDEEM_CODE
    
    elif data == "menu_bypass":
        if db.has_bypass(user_id):
            await query.message.reply_text(
                "<blockquote>🛡️ <b>BYPASS ACTIVE</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ Your bypass mode is currently active.\n\n"
                "🔓 <b>Benefits:</b>\n"
                "   • No spam restrictions\n"
                "   • Unlimited searches\n"
                "   • Priority access\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "💫 <i>Enjoy unlimited access!</i></blockquote>",
                parse_mode='HTML'
            )
        else:
            result = await bypass_system.request_bypass(user_id, context)
            await query.message.reply_text(result['message'], parse_mode='Markdown')
    
    elif data == "menu_help":
        await query.message.reply_text(
            "<blockquote>📖 <b>HELP & COMMANDS</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>📌 Basic Commands:</b>\n"
            "   /start - Start the bot\n"
            "   /daily - Claim daily reward\n"
            "   /balance - Check credits\n"
            "   /bypass - Activate bypass\n"
            "   /refer - Get referral link\n"
            "   /redeem - Redeem code\n\n"
            "<b>🔍 Search Commands:</b>\n"
            "   Send a phone number → Phone lookup\n"
            "   Send @username → User lookup\n"
            "   /ff [UID] → Free Fire info\n\n"
            "<b>🚀 Rocket Commands:</b>\n"
            "   /bomb [number] - Start rockets\n"
            "   /stopbomb - Stop rockets\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👑 <b>Developer:</b> {__import__('config').DEV_USERNAME}\n"
            f"🌐 <b>Website:</b> <a href='{__import__('config').WEBSITE_URL}'>Click Here</a>\n"
            f"👥 <b>Group:</b> <a href='{__import__('config').GROUP_URL}'>Join Now</a>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 <i>Need more help? Contact @XITDARKX77</i></blockquote>",
            parse_mode='HTML'
        )
    
    elif data == "menu_owner":
        await query.message.reply_text(
            f"<blockquote>👑 <b>DEVELOPER INFO</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🤖 <b>Bot:</b> @TheDarkX77_bot\n"
            f"👤 <b>Dev:</b> {__import__('config').DEV_USERNAME}\n"
            f"📱 <b>Instagram:</b> {__import__('config').DEV_INSTAGRAM}\n"
            f"🌐 <b>Website:</b> <a href='{__import__('config').WEBSITE_URL}'>bio.site/TheDarkX77Cheat</a>\n"
            f"👥 <b>Group:</b> <a href='{__import__('config').GROUP_URL}'>Join Here</a>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💫 <i>Powered by The Dark X77 Team</i></blockquote>",
            parse_mode='HTML'
        )
    
    elif data == "menu_stats":
        user = db.get_user(user_id)
        bypass_status = "ACTIVE" if db.has_bypass(user_id) else "INACTIVE"
        await query.message.reply_text(
            f"<blockquote>🏆 <b>USER STATISTICS</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
            f"📊 <b>Total Searches:</b> {user['total_searches'] if user else 0}\n"
            f"💰 <b>Total Credits:</b> {db.get_credits(user_id)}\n"
            f"🛡️ <b>Bypass Status:</b> {bypass_status}\n"
            f"📅 <b>Joined:</b> {user['created_at'] if user else 'N/A'}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💫 <i>Keep using to unlock more features!</i></blockquote>",
            parse_mode='HTML'
        )
    
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle auto-reply for phone numbers and usernames"""
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Phone number pattern
    phone_pattern = r'^[\+]?[0-9\s\-\(\)]{10,20}$'
    # Username pattern
    username_pattern = r'^@[\w_]{5,32}$'
    
    # Check for phone number
    if re.match(phone_pattern, message_text.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')):
        result = await search_by_phone(message_text, user_id, context)
        await update.message.reply_text(result, parse_mode='Markdown')
    
    # Check for username
    elif re.match(username_pattern, message_text):
        result = await search_by_username(message_text, user_id, context)
        await update.message.reply_text(result, parse_mode='Markdown')
    
    # Check for bomb command in message
    elif message_text.lower().startswith('bomb '):
        number = message_text.split(' ')[1]
        await update.message.reply_text(
            f"<blockquote>🚀 <b>ROCKETS ACTIVATED</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📞 <b>Target:</b> <code>{number}</code>\n"
            f"💣 <b>Status:</b> Sending rockets...\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ <i>Use /stopbomb to stop</i></blockquote>",
            parse_mode='HTML'
        )