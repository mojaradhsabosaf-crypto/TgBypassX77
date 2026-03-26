# utils.py
import requests
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from anti_spam import anti_spam
from bypass import bypass_system

db = Database()

async def get_number_info(phone_number: str) -> dict:
    """Get phone number information (Mock API - Replace with real API)"""
    # TODO: Replace with real API like numverify.com
    # Example: response = requests.get(f"http://apilayer.net/api/validate?access_key=YOUR_KEY&number={phone_number}")
    
    # Mock response for demonstration
    mock_data = {
        "valid": True,
        "number": phone_number,
        "country": "India",
        "country_code": "+91",
        "carrier": "Jio",
        "location": "Mumbai",
        "line_type": "mobile"
    }
    
    # Simulate API delay
    await asyncio.sleep(1)
    
    return mock_data

async def get_username_info(username: str, context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get Telegram username information"""
    try:
        # Remove @ if present
        username = username.replace('@', '')
        
        # Get chat info
        chat = await context.bot.get_chat(f"@{username}")
        
        # Get profile photos
        photos = await context.bot.get_user_profile_photos(chat.id, limit=1)
        photo_file_id = photos.photos[0][0].file_id if photos.photos else None
        
        return {
            "success": True,
            "user_id": chat.id,
            "username": chat.username,
            "first_name": chat.first_name,
            "last_name": chat.last_name,
            "bio": chat.bio if hasattr(chat, 'bio') else "No bio",
            "photo": photo_file_id,
            "is_bot": chat.is_bot if hasattr(chat, 'is_bot') else False
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def get_freefire_info(uid: str) -> dict:
    """Get Free Fire information (Mock API - Replace with real API)"""
    # TODO: Replace with real Free Fire API
    # Example: response = requests.get(f"https://api.freefire.com/v1/user/{uid}")
    
    mock_data = {
        "success": True,
        "uid": uid,
        "nickname": f"Player_{uid[-4:]}",
        "level": 65,
        "xp": 24500,
        "rank": "Heroic",
        "likes": 1240,
        "region": "Asia"
    }
    
    await asyncio.sleep(0.5)
    return mock_data

async def search_by_phone(phone: str, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle phone number search with credit deduction"""
    # Check bypass
    has_bypass = db.has_bypass(user_id)
    
    if not has_bypass:
        # Check spam limit
        can_search, cooldown = await anti_spam.check_search_limit(user_id)
        if not can_search:
            return f"⏳ **Rate Limited!**\nPlease wait {cooldown} seconds before searching again."
        
        # Deduct credits
        if not db.deduct_credits(user_id, 1):
            return "❌ **Insufficient Credits!**\n\nUse /daily to get free credits or redeem a code."
    
    # Log search
    db.log_search(user_id, "phone", phone)
    
    # Get info
    info = await get_number_info(phone)
    
    # Format response
    response = f"""
📞 **PHONE NUMBER INFORMATION**

━━━━━━━━━━━━━━━━━━━━
📱 **Number:** `{info['number']}`
🌍 **Country:** {info['country']} ({info['country_code']})
📡 **Carrier:** {info['carrier']}
📍 **Location:** {info['location']}
🔌 **Line Type:** {info['line_type']}
✅ **Valid:** {'Yes' if info['valid'] else 'No'}

━━━━━━━━━━━━━━━━━━━━
🔍 *Searched by: {user_id}*
🕐 *Time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    if not has_bypass:
        response += f"\n💰 **Credits Remaining:** {db.get_credits(user_id)}"
    
    return response

async def search_by_username(username: str, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle username search with credit deduction"""
    # Check bypass
    has_bypass = db.has_bypass(user_id)
    
    if not has_bypass:
        # Check spam limit
        can_search, cooldown = await anti_spam.check_search_limit(user_id)
        if not can_search:
            return f"⏳ **Rate Limited!**\nPlease wait {cooldown} seconds before searching again."
        
        # Deduct credits
        if not db.deduct_credits(user_id, 1):
            return "❌ **Insufficient Credits!**\n\nUse /daily to get free credits or redeem a code."
    
    # Log search
    db.log_search(user_id, "username", username)
    
    # Get info
    info = await get_username_info(username, context)
    
    if not info['success']:
        return f"❌ **Error:** {info['error']}"
    
    # Format response
    response = f"""
👤 **TELEGRAM USER INFORMATION**

━━━━━━━━━━━━━━━━━━━━
🆔 **User ID:** `{info['user_id']}`
👤 **Username:** @{info['username']}
📛 **Name:** {info['first_name']} {info['last_name'] if info['last_name'] else ''}
📝 **Bio:** {info['bio']}
🤖 **Bot:** {'Yes' if info['is_bot'] else 'No'}

━━━━━━━━━━━━━━━━━━━━
🔍 *Searched by: {user_id}*
🕐 *Time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    if not has_bypass:
        response += f"\n💰 **Credits Remaining:** {db.get_credits(user_id)}"
    
    return response

async def x11_multiplier(user_id: int) -> str:
    """Apply X11 multiplier (5 credits for 55 credits)"""
    credits = db.get_credits(user_id)
    
    if credits >= 5:
        db.deduct_credits(user_id, 5)
        db.add_credits(user_id, 55)
        new_credits = db.get_credits(user_id)
        
        return f"""
⚡ **X11 MULTIPLIER ACTIVATED!**

━━━━━━━━━━━━━━━━━━━━
💰 **Cost:** 5 credits
🎁 **Reward:** +55 credits

📊 **Credits Change:**
   Before: {credits}
   After: {new_credits}
   Gain: +50 credits

━━━━━━━━━━━━━━━━━━━━
✨ *Thank you for using X11 Multiplier!*
"""
    else:
        return f"""
❌ **Insufficient Credits for X11 Multiplier!**

━━━━━━━━━━━━━━━━━━━━
⚡ **X11 Cost:** 5 credits
🎁 **Reward:** 55 credits

💰 **Your Balance:** {credits}
📉 **Missing:** {5 - credits} credits

━━━━━━━━━━━━━━━━━━━━
💡 *Get more credits via:*
   • Daily reward: /daily
   • Refer friends: /refer
   • Redeem codes: /redeem
"""