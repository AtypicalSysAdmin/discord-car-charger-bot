import sqlite3
import os
from datetime import datetime, timezone, timedelta
import pytz

class SharedState:
    def __init__(self, db_path="bot_state.db"):
        self.db_path = db_path
        self.tz_pacific = pytz.timezone('US/Pacific')
        self.start_time = datetime.now(timezone.utc)
        
        # In-memory defaults
        self.charging_active = False
        self.charging_start_time = None
        self.current_shift = None  # "day" or "night"
        self.next_target_time = None
        self.next_interval_time = None
        self.initial_reminder_sent = False
        self.is_muted = False
        self.muted_until = None
        self.last_reminder_date = None
        self.last_reminder_id = None
        
        self._init_db()
        self._load_state()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def _load_state(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM state")
            rows = cursor.fetchall()
            data = dict(rows)
            
            if "charging_active" in data:
                self.charging_active = data["charging_active"] == "True"
            if "charging_start_time" in data and data["charging_start_time"] != "None":
                self.charging_start_time = datetime.fromisoformat(data["charging_start_time"])
            if "current_shift" in data and data["current_shift"] != "None":
                self.current_shift = data["current_shift"]
            if "is_muted" in data:
                self.is_muted = data["is_muted"] == "True"
            if "muted_until" in data and data["muted_until"] != "None":
                self.muted_until = datetime.fromisoformat(data["muted_until"])
            if "next_target_time" in data and data["next_target_time"] != "None":
                self.next_target_time = datetime.fromisoformat(data["next_target_time"])
            if "next_interval_time" in data and data["next_interval_time"] != "None":
                self.next_interval_time = datetime.fromisoformat(data["next_interval_time"])
            if "initial_reminder_sent" in data:
                self.initial_reminder_sent = data["initial_reminder_sent"] == "True"
            if "last_reminder_date" in data and data["last_reminder_date"] != "None":
                self.last_reminder_date = datetime.fromisoformat(data["last_reminder_date"]).date()
            if "last_reminder_id" in data and data["last_reminder_id"] != "None":
                self.last_reminder_id = int(data["last_reminder_id"])

    def save(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("charging_active", str(self.charging_active)))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("charging_start_time", self.charging_start_time.isoformat() if self.charging_start_time else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("current_shift", str(self.current_shift) if self.current_shift else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("is_muted", str(self.is_muted)))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("muted_until", self.muted_until.isoformat() if self.muted_until else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("next_target_time", self.next_target_time.isoformat() if self.next_target_time else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("next_interval_time", self.next_interval_time.isoformat() if self.next_interval_time else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("initial_reminder_sent", str(self.initial_reminder_sent)))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("last_reminder_date", self.last_reminder_date.isoformat() if self.last_reminder_date else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("last_reminder_id", str(self.last_reminder_id) if self.last_reminder_id else "None"))
            conn.commit()

    def calculate_shift_and_target(self, now_utc=None):
        """
        Determines current parking shift and target reminder time based on Pacific time.
        Shifts:
          - Day Shift: 6:00 AM to 6:00 PM (18:00). Target reminder is 5:00 PM (17:00).
            If plugged in at/after 5:00 PM, reminder is due immediately.
          - Night Shift: 6:00 PM (18:00) to 6:00 AM. Target reminder is 10:00 PM (22:00).
            If plugged in at/after 10:00 PM (or between midnight and 6:00 AM), reminder is due immediately.
        """
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        now_pacific = now_utc.astimezone(self.tz_pacific)
        
        hour = now_pacific.hour
        if 6 <= hour < 18:
            shift = "day"
            target_pacific = now_pacific.replace(hour=17, minute=0, second=0, microsecond=0)
            if now_pacific >= target_pacific:
                target_utc = now_utc
            else:
                target_utc = target_pacific.astimezone(timezone.utc)
        else:
            shift = "night"
            if hour >= 18:
                target_pacific = now_pacific.replace(hour=22, minute=0, second=0, microsecond=0)
                if now_pacific >= target_pacific:
                    target_utc = now_utc
                else:
                    target_utc = target_pacific.astimezone(timezone.utc)
            else:  # 0 <= hour < 6 (past midnight)
                target_utc = now_utc
                
        return shift, target_utc

    def set_plugged(self):
        now_utc = datetime.now(timezone.utc)
        shift, target_utc = self.calculate_shift_and_target(now_utc)
        
        self.charging_active = True
        self.charging_start_time = now_utc
        self.current_shift = shift
        self.next_target_time = target_utc
        self.next_interval_time = None
        self.initial_reminder_sent = False
        self.is_muted = False
        self.muted_until = None
        self.last_reminder_id = None
        self.last_reminder_date = None
        self.save()
        return shift, target_utc

    def set_unplugged(self):
        self.charging_active = False
        self.charging_start_time = None
        self.current_shift = None
        self.next_target_time = None
        self.next_interval_time = None
        self.initial_reminder_sent = False
        self.is_muted = False
        self.muted_until = None
        self.save()

    def set_mute(self, tz=None):
        if tz is None:
            tz = self.tz_pacific
        now_pacific = datetime.now(timezone.utc).astimezone(tz)
        hour = now_pacific.hour
        
        # If in day shift (6 AM to 6 PM), mute until 6 PM
        if 6 <= hour < 18:
            mute_until_pacific = now_pacific.replace(hour=18, minute=0, second=0, microsecond=0)
        else:
            # If in night shift (6 PM to 6 AM)
            if hour >= 18:
                mute_until_pacific = (now_pacific + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
            else:
                mute_until_pacific = now_pacific.replace(hour=6, minute=0, second=0, microsecond=0)
                
        self.is_muted = True
        self.muted_until = mute_until_pacific.astimezone(timezone.utc)
        self.save()
        return mute_until_pacific

    def set_unmute(self):
        self.is_muted = False
        self.muted_until = None
        self.save()

state = SharedState()
