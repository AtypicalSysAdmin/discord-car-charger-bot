import sqlite3
import os
from datetime import datetime, timezone, timedelta

class SharedState:
    def __init__(self, db_path="bot_state.db"):
        self.db_path = db_path
        self.start_time = datetime.now(timezone.utc)
        
        # In-memory defaults
        self.charging_active = False
        self.charging_start_time = None
        self.next_target_time = None
        self.next_interval_time = None
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
            if "is_muted" in data:
                self.is_muted = data["is_muted"] == "True"
            if "muted_until" in data and data["muted_until"] != "None":
                self.muted_until = datetime.fromisoformat(data["muted_until"])
            if "next_target_time" in data and data["next_target_time"] != "None":
                self.next_target_time = datetime.fromisoformat(data["next_target_time"])
            if "next_interval_time" in data and data["next_interval_time"] != "None":
                self.next_interval_time = datetime.fromisoformat(data["next_interval_time"])
            if "last_reminder_date" in data and data["last_reminder_date"] != "None":
                self.last_reminder_date = datetime.fromisoformat(data["last_reminder_date"]).date()
            if "last_reminder_id" in data and data["last_reminder_id"] != "None":
                self.last_reminder_id = int(data["last_reminder_id"])

    def save(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("charging_active", str(self.charging_active)))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("charging_start_time", self.charging_start_time.isoformat() if self.charging_start_time else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("is_muted", str(self.is_muted)))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("muted_until", self.muted_until.isoformat() if self.muted_until else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("next_target_time", self.next_target_time.isoformat() if self.next_target_time else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("next_interval_time", self.next_interval_time.isoformat() if self.next_interval_time else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("last_reminder_date", self.last_reminder_date.isoformat() if self.last_reminder_date else "None"))
            conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)", ("last_reminder_id", str(self.last_reminder_id) if self.last_reminder_id else "None"))
            conn.commit()

    def set_plugged(self):
        self.charging_active = True
        self.charging_start_time = datetime.now(timezone.utc)
        self.is_muted = False
        self.muted_until = None
        self.save()

    def set_unplugged(self):
        self.charging_active = False
        self.charging_start_time = None
        self.next_interval_time = None
        self.is_muted = False
        self.muted_until = None
        self.save()

    def set_mute(self, tz_pacific):
        now_pacific = datetime.now(timezone.utc).astimezone(tz_pacific)
        mute_until = now_pacific.replace(hour=6, minute=0, second=0, microsecond=0)
        if now_pacific >= mute_until:
            mute_until += timedelta(days=1)
        self.is_muted = True
        self.muted_until = mute_until.astimezone(timezone.utc)
        self.save()
        return mute_until

    def set_unmute(self):
        self.is_muted = False
        self.muted_until = None
        self.save()

state = SharedState()
