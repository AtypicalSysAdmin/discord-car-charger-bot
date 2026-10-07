from flask import Flask, render_template, jsonify, make_response, send_from_directory
from datetime import datetime, timezone
import pytz
from state import state
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
import asyncio

app = Flask(__name__)
tz_pacific = pytz.timezone('US/Pacific')

# Global pointer to the bot instance
bot_ptr = None

def get_status_data():
    now = datetime.now(timezone.utc)
    now_pacific = now.astimezone(tz_pacific)
    uptime_delta = now - state.start_time
    
    # Raw start time for smooth client-side ticking
    start_utc = None
    if state.charging_active and state.charging_start_time:
        start_time = state.charging_start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        start_utc = start_time.timestamp()

    # Next Notification (Absolute Time)
    notify_time_str = "N/A"
    if state.charging_active:
        target = None
        if not state.initial_reminder_sent and state.next_target_time:
            target = state.next_target_time
        elif state.next_interval_time:
            target = state.next_interval_time
        elif state.next_target_time:
            target = state.next_target_time

        if target:
            target_aware = target if target.tzinfo else target.replace(tzinfo=timezone.utc)
            if target_aware <= now:
                notify_time_str = "Due now"
            else:
                notify_time_str = target_aware.astimezone(tz_pacific).strftime("%I:%M %p")

    shift_display = None
    if state.charging_active and state.current_shift:
        shift_display = "Day Shift (6 AM - 6 PM)" if state.current_shift == "day" else "Night Shift (6 PM - 6 AM)"

    return {
        "bot_uptime": f"{uptime_delta.days}d {uptime_delta.seconds // 3600}h {(uptime_delta.seconds // 60) % 60}m",
        "charging": state.charging_active,
        "charging_start_utc": start_utc,
        "current_shift": state.current_shift,
        "shift_display": shift_display,
        "next_notification": notify_time_str,
        "is_muted": state.is_muted,
        "muted_until": state.muted_until.astimezone(tz_pacific).strftime("%I:%M %p") if state.muted_until else None
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(BASE_DIR, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/status')
def status():
    data = get_status_data()
    response = make_response(jsonify(data))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/action/plugged', methods=['POST'])
def action_plugged():
    state.set_plugged()
    return jsonify({"status": "success"})

@app.route('/api/action/unplugged', methods=['POST'])
def action_unplugged():
    state.set_unplugged()
    return jsonify({"status": "success"})

@app.route('/api/action/mute', methods=['POST'])
def action_mute():
    state.set_mute(tz_pacific)
    return jsonify({"status": "success"})

@app.route('/api/action/unmute', methods=['POST'])
def action_unmute():
    state.set_unmute()
    return jsonify({"status": "success"})

@app.route('/api/action/clear_history', methods=['POST'])
def action_clear_history():
    if bot_ptr:
        async def do_clear():
            user = await bot_ptr.fetch_user(int(bot_ptr.user_id))
            channel = user.dm_channel or await user.create_dm()
            await bot_ptr._clear_history(channel)
        
        asyncio.run_coroutine_threadsafe(do_clear(), bot_ptr.loop)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Bot pointer not initialized"}), 500

def run_dashboard(bot_instance=None):
    global bot_ptr
    bot_ptr = bot_instance
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
