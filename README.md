# EV Charger Discord Bot 🚗⚡

A robust Discord-integrated EV charging reminder system with a real-time glassmorphic dashboard. Supports dual-shift parking schedules (6 AM – 6 PM & 6 PM – 6 AM).

## ✨ Features

-   **Discord Command System**: Simple `/plugged` and `/unplugged` commands to manage charging state with automatic DM history cleanup.
-   **Smart Shift Detection**:
    -   **Day Shift (6:00 AM – 6:00 PM)**: Sets reminder for **5:00 PM** (1 hour before cutoff), nagging every 15 minutes to pick up your car.
    -   **Night Shift (6:00 PM – 6:00 AM)**: Sets reminder for **10:00 PM**, nagging every 15 minutes until unplugged.
-   **Reactive & Immediate Alerts**: If you plug in after the target time (e.g. after 5:00 PM in day shift, or after 10:00 PM in night shift), reminders begin immediately.
-   **Persistent 15-Minute Nags**: Continues sending 15-minute reminders until the `/unplugged` command is triggered.
-   **Live Dashboard**: A beautiful, premium dark-mode web interface to monitor:
    -   **System Uptime**: Total bot runtime.
    -   **Vehicle State & Parking Shift**: Live status and detected shift (Day Shift vs. Night Shift).
    -   **Charging Session**: Real-time timer showing exactly how long you've been plugged in.
    -   **Next Notification**: Accurate clock time (US/Pacific) showing exactly when the next alert will trigger.
-   **Universal Time Management**: Uses timezone-aware UTC logic for perfect reliability across servers.

## 🚀 Quick Deploy

Use the provided PowerShell script for automated deployment to a remote Linux server (e.g., Kali, Ubuntu, Raspberry Pi).

```powershell
.\deploy.ps1
```

**The script handles:**
1.  Verifying project structure.
2.  Transferring code and assets via SSH.
3.  Setting up the remote Python virtual environment.
4.  Installing dependencies.
5.  Configuring `@reboot` cron jobs for zero-maintenance operation.

## 🛠 Tech Stack

-   **Bot**: Python, `discord.py` (Slash Commands).
-   **Dashboard**: Flask, Vanilla CSS (Glassmorphism), JavaScript (1s visual polling).
-   **State Management**: Shared memory-safe object for cross-thread communication.
-   **Time Handling**: `pytz` + Aware UTC `datetime`.

## ⚙️ Configuration

Set your environment variables in the `.env` file:

```env
DISCORD_TOKEN=your_token_here
YOUR_USER_ID=your_id_here
REMINDER_HOUR=22
REMINDER_MINUTE=30
DASHBOARD_PORT=5000
```

## 📋 Commands

-   `/plugged`: Enable reminders and start the charging session timer.
-   `/unplugged`: Stop reminders and reset the session.

## 📈 Monitoring

Access the live dashboard at `http://your-server-ip:5000`. 
The dashboard automatically updates every 5 seconds from the server while providing smooth 1-second visual ticks for timers.

---
*Created with focus on Reliability and User Experience.*