# database.py
import sqlite3
import datetime
from contextlib import contextmanager
from config import STARTING_CREDITS

class Database:
    def __init__(self, db_name="bot.db"):
        self.db_name = db_name
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize all database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    credits INTEGER DEFAULT 10,
                    last_daily TEXT,
                    total_searches INTEGER DEFAULT 0,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    warnings INTEGER DEFAULT 0,
                    is_bypass TEXT DEFAULT 'false',
                    bypass_until TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Redeem codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS redeem_codes (
                    code TEXT PRIMARY KEY,
                    credits INTEGER,
                    used_by INTEGER,
                    used_at TEXT,
                    is_used INTEGER DEFAULT 0
                )
            ''')
            
            # Search logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    search_type TEXT,
                    query TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Spam warnings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    warning_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bypass logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bypass_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def get_user(self, user_id):
        """Get user data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()
    
    def create_user(self, user_id, username, first_name, last_name, referred_by=None):
        """Create new user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            referral_code = f"X77{user_id}"
            
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, credits, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, STARTING_CREDITS, referral_code, referred_by))
            
            conn.commit()
            
            if referred_by:
                self.add_credits(referred_by, 5)
            
            return self.get_user(user_id)
    
    def update_credits(self, user_id, amount):
        """Update user credits"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET credits = credits + ? WHERE user_id = ?
            ''', (amount, user_id))
            conn.commit()
    
    def get_credits(self, user_id):
        """Get user credits"""
        user = self.get_user(user_id)
        return user['credits'] if user else None
    
    def add_credits(self, user_id, amount):
        """Add credits to user"""
        self.update_credits(user_id, amount)
    
    def deduct_credits(self, user_id, amount):
        """Deduct credits from user"""
        current = self.get_credits(user_id)
        if current and current >= amount:
            self.update_credits(user_id, -amount)
            return True
        return False
    
    def update_daily(self, user_id):
        """Update daily claim timestamp"""
        today = datetime.date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_daily = ? WHERE user_id = ?
            ''', (today, user_id))
            conn.commit()
    
    def can_claim_daily(self, user_id):
        """Check if user can claim daily reward"""
        user = self.get_user(user_id)
        if not user or not user['last_daily']:
            return True
        return user['last_daily'] != datetime.date.today().isoformat()
    
    def add_warning(self, user_id, warning_type="spam"):
        """Add warning to user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO spam_warnings (user_id, warning_type)
                VALUES (?, ?)
            ''', (user_id, warning_type))
            
            cursor.execute('''
                UPDATE users SET warnings = warnings + 1 WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            
            user = self.get_user(user_id)
            return user['warnings'] if user else 0
    
    def reset_warnings(self, user_id):
        """Reset user warnings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET warnings = 0 WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def set_bypass(self, user_id, status, duration_minutes=10):
        """Set bypass status for user"""
        bypass_until = None
        if status:
            bypass_until = (datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET is_bypass = ?, bypass_until = ? WHERE user_id = ?
            ''', (str(status).lower(), bypass_until, user_id))
            conn.commit()
            
            cursor.execute('''
                INSERT INTO bypass_logs (user_id, action)
                VALUES (?, ?)
            ''', (user_id, "activate" if status else "deactivate"))
            conn.commit()
    
    def has_bypass(self, user_id):
        """Check if user has active bypass"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        if user['is_bypass'] == 'true':
            if user['bypass_until']:
                bypass_until = datetime.datetime.fromisoformat(user['bypass_until'])
                if bypass_until > datetime.datetime.now():
                    return True
                else:
                    self.set_bypass(user_id, False)
                    return False
            return True
        return False
    
    def log_search(self, user_id, search_type, query):
        """Log search activity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO search_logs (user_id, search_type, query)
                VALUES (?, ?, ?)
            ''', (user_id, search_type, query))
            conn.commit()
            
            cursor.execute('''
                UPDATE users SET total_searches = total_searches + 1 WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def get_recent_searches(self, user_id, minutes=1):
        """Get number of searches in last X minutes"""
        time_ago = (datetime.datetime.now() - datetime.timedelta(minutes=minutes)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM search_logs 
                WHERE user_id = ? AND created_at > ?
            ''', (user_id, time_ago))
            result = cursor.fetchone()
            return result['count']
    
    def add_redeem_code(self, code, credits):
        """Add redeem code to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO redeem_codes (code, credits)
                VALUES (?, ?)
            ''', (code, credits))
            conn.commit()
    
    def use_redeem_code(self, code, user_id):
        """Use redeem code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM redeem_codes WHERE code = ? AND is_used = 0
            ''', (code,))
            result = cursor.fetchone()
            
            if result:
                cursor.execute('''
                    UPDATE redeem_codes SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                ''', (user_id, code))
                conn.commit()
                return result['credits']
            return None