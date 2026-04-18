from flask import Flask, render_template, jsonify, make_response, send_from_directory
from datetime import datetime, timezone
import pytz
from state import state
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
tz_pacific = pytz.timezone('US/Pacific')

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
        possible_times = []
        if state.next_target_time:
            possible_times.append(state.next_target_time)
        if state.next_interval_time:
            possible_times.append(state.next_interval_time)
            
        if possible_times:
            # We want the absolute time of the EARLIEST future notification
            # Ensure all are converted to aware UTC for comparison
            now_aware = datetime.now(timezone.utc)
            future_times = [t if t.tzinfo else t.replace(tzinfo=timezone.utc) for t in possible_times]
            future_times = [t for t in future_times if t > now_aware]
            
            if future_times:
                earliest = min(future_times)
                # Convert to Pacific for display
                earliest_pacific = earliest.astimezone(tz_pacific)
                notify_time_str = earliest_pacific.strftime("%I:%M %p") # e.g. 10:30 PM

    return {
        "bot_uptime": f"{uptime_delta.days}d {uptime_delta.seconds // 3600}h {(uptime_delta.seconds // 60) % 60}m",
        "charging": state.charging_active,
        "charging_start_utc": start_utc,
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

def run_dashboard():
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
