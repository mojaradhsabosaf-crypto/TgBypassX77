# bypass.py
import asyncio
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import Database

db = Database()

class BypassSystem:
    def __init__(self):
        self.bypass_requests = {}  # user_id: last_request_time
    
    async def request_bypass(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """Request bypass access"""
        now = datetime.datetime.now()
        
        # Check cooldown
        if user_id in self.bypass_requests:
            last_req = self.bypass_requests[user_id]
            if (now - last_req).total_seconds() < 300:  # 5 minutes cooldown
                remaining = 300 - (now - last_req).total_seconds()
                return {
                    "success": False,
                    "message": f"⏳ Please wait {int(remaining)} seconds before requesting bypass again!"
                }
        
        self.bypass_requests[user_id] = now
        
        # Check user credits
        credits = db.get_credits(user_id)
        if credits and credits >= 10:
            # Activate bypass
            db.set_bypass(user_id, True, 30)  # 30 minutes bypass
            db.deduct_credits(user_id, 10)
            
            return {
                "success": True,
                "message": "✅ **BYPASS ACTIVATED!**\n\n"
                          "You now have bypass access for 30 minutes!\n"
                          "- No spam restrictions\n"
                          "- Unlimited searches\n"
                          "- Priority access\n\n"
                          f"Credits deducted: 10\n"
                          f"Remaining credits: {db.get_credits(user_id)}"
            }
        else:
            return {
                "success": False,
                "message": "❌ **Insufficient Credits!**\n\n"
                          f"Bypass costs 10 credits\n"
                          f"Your balance: {credits if credits else 0}\n\n"
                          "Get more credits via:\n"
                          "- Daily reward (+2)\n"
                          "- Referral system\n"
                          "- Redeem codes"
            }
    
    async def check_bypass_status(self, user_id: int) -> dict:
        """Check bypass status"""
        has_bypass = db.has_bypass(user_id)
        user = db.get_user(user_id)
        
        if has_bypass:
            return {
                "active": True,
                "expires": user['bypass_until'] if user else None
            }
        else:
            return {
                "active": False,
                "expires": None
            }
    
    async def deactivate_bypass(self, user_id: int):
        """Deactivate bypass"""
        db.set_bypass(user_id, False)

bypass_system = BypassSystem()