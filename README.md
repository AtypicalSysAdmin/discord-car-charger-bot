# EV Charger Discord Bot 🚗⚡

A robust Discord-integrated EV charging reminder system with a real-time glassmorphic dashboard. Designed to ensure you never forget to unplug your car at night.

## ✨ Features

-   **Discord Command System**: Simple `/plugged` and `/unplugged` commands to manage charging state.
-   **Smart Daily Reminders**: Sends a high-priority notification at a configurable time (e.g., 10:30 PM).
-   **Reactive Logic**: If you plug in *after* the scheduled time, the bot detects it within 30 seconds and notifies you immediately.
-   **Persistent Nags**: Once the daily reminder is sent, the bot will gently "nag" you every 15 minutes until the `/unplugged` command is run.
-   **Live Dashboard**: A beautiful, premium dark-mode web interface to monitor:
    -   **System Uptime**: Total bot runtime.
    -   **Vehicle State**: Live status (Plugged In / Unplugged).
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