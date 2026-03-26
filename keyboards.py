# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu():
    """Main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📞 NUMBER INFO", callback_data="menu_number"),
            InlineKeyboardButton("👤 USERNAME INFO", callback_data="menu_username")
        ],
        [
            InlineKeyboardButton("🎁 DAILY", callback_data="menu_daily"),
            InlineKeyboardButton("⚡ X11 MULTIPLIER", callback_data="menu_x11")
        ],
        [
            InlineKeyboardButton("🚀 ROCKETS", callback_data="menu_rocket"),
            InlineKeyboardButton("🎮 FREE FIRE", callback_data="menu_freefire")
        ],
        [
            InlineKeyboardButton("💰 BALANCE", callback_data="menu_balance"),
            InlineKeyboardButton("🎟️ REDEEM", callback_data="menu_redeem")
        ],
        [
            InlineKeyboardButton("👥 REFERRALS", callback_data="menu_referrals"),
            InlineKeyboardButton("🛡️ BYPASS", callback_data="menu_bypass")
        ],
        [
            InlineKeyboardButton("📖 HELP", callback_data="menu_help"),
            InlineKeyboardButton("👑 OWNER", callback_data="menu_owner")
        ],
        [
            InlineKeyboardButton("➡️ NEXT PAGE", callback_data="next_page")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_second_page():
    """Second page keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 TG ID INFO", callback_data="menu_tgid"),
            InlineKeyboardButton("📧 EMAIL INFO", callback_data="menu_email")
        ],
        [
            InlineKeyboardButton("🌐 PINCODE INFO", callback_data="menu_pincode"),
            InlineKeyboardButton("🆔 PAN INFO", callback_data="menu_pan")
        ],
        [
            InlineKeyboardButton("📱 INSTAGRAM", callback_data="menu_instagram"),
            InlineKeyboardButton("🎮 FF DRESS", callback_data="menu_ff_dress")
        ],
        [
            InlineKeyboardButton("🏆 MY STATS", callback_data="menu_stats"),
            InlineKeyboardButton("⭐ PREMIUM", callback_data="menu_premium")
        ],
        [
            InlineKeyboardButton("⬅️ PREV PAGE", callback_data="prev_page")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_menu():
    """Back button only"""
    keyboard = [
        [InlineKeyboardButton("🔙 BACK TO MENU", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_button():
    """Cancel button"""
    keyboard = [
        [InlineKeyboardButton("❌ CANCEL", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)