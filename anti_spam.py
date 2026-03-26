# anti_spam.py
import asyncio
import datetime
from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from database import Database

db = Database()

class AntiSpamSystem:
    def __init__(self):
        self.user_messages = {}  # user_id: list of timestamps
        self.group_warnings = {}  # group_id: {user_id: warnings}
    
    async def check_user_spam(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is spamming (returns True if spam detected)"""
        now = datetime.datetime.now()
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Clean old messages
        self.user_messages[user_id] = [
            ts for ts in self.user_messages[user_id] 
            if (now - ts).total_seconds() < 5
        ]
        
        # Check spam
        if len(self.user_messages[user_id]) >= 5:
            return True
        
        self.user_messages[user_id].append(now)
        return False
    
    async def check_search_limit(self, user_id: int) -> tuple:
        """Check if user exceeded search limit (bool, remaining_time)"""
        recent = db.get_recent_searches(user_id, 1)
        
        if recent >= 3:
            return False, 60  # 60 seconds cooldown
        
        return True, 0
    
    async def warn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str):
        """Warn user in group"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        warnings = db.add_warning(user_id, reason)
        remaining = 3 - warnings
        
        if warnings >= 3:
            # Ban user from group
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                await update.message.reply_text(
                    f"🚫 **User {update.effective_user.first_name} has been banned!**\n"
                    f"Reason: 3 warnings exceeded - {reason}",
                    parse_mode='Markdown'
                )
                db.reset_warnings(user_id)
            except Exception as e:
                print(f"Error banning user: {e}")
        else:
            await update.message.reply_text(
                f"⚠️ **Warning {warnings}/3**\n"
                f"Reason: {reason}\n"
                f"Remaining warnings: {remaining}",
                parse_mode='Markdown'
            )
    
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group messages for spam detection"""
        if not update.message or not update.message.text:
            return
        
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if user has bypass
        if db.has_bypass(user_id):
            return True
        
        # Check for spam
        is_spam = await self.check_user_spam(user_id, context)
        
        if is_spam:
            await self.warn_user(update, context, "Spamming messages")
            try:
                await update.message.delete()
            except:
                pass
            return False
        
        # Check for phone number in message
        import re
        phone_pattern = r'[\+]?[0-9]{10,15}'
        username_pattern = r'@[\w_]+'
        
        if re.search(phone_pattern, update.message.text):
            return "phone"
        elif re.search(username_pattern, update.message.text):
            return "username"
        
        return True

anti_spam = AntiSpamSystem()