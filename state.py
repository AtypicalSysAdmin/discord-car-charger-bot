from datetime import datetime, timezone

class SharedState:
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.charging_active = False
        self.charging_start_time = None
        self.next_target_time = None
        self.next_interval_time = None

state = SharedState()
