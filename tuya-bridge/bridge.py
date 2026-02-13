import os
import time
import threading
import json
import tinytuya
import paho.mqtt.client as mqtt
from flask import Flask, render_template_string

# --- CONFIGURATION ---
DEVICE_ID = os.getenv('DEVICE_ID', 'eb43fe0ed2c8be5220tg2u')
IP_ADDRESS = os.getenv('IP_ADDRESS', '192.168.1.27')
LOCAL_KEY = os.getenv('LOCAL_KEY', 'xxx')

MQTT_HOST = os.getenv('MQTT_HOST', '192.168.1.22') 
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER', '')
MQTT_PASS = os.getenv('MQTT_PASS', '')

app = Flask(__name__)

# Global State for Multi-Clamp Monitoring
stats = {
    "voltage": 0,
    "clamp1_power": 0,
    "clamp1_current": 0,
    "clamp2_power": 0,
    "clamp2_current": 0,
    "online": False,
    "raw_dps": {}
}

def tuya_worker():
    global stats
    # Initialize Device
    d = tinytuya.Device(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
    d.set_version(3.3)
    
    mqtt_c = mqtt.Client()
    if MQTT_USER and MQTT_PASS:
        mqtt_c.username_pw_set(MQTT_USER, MQTT_PASS)
    
    try:
        mqtt_c.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_c.loop_start()
    except Exception as e:
        print(f"MQTT Connection Failed: {e}")

    while True:
        try:
            data = d.status()
            if data and 'dps' in data:
                dps = data['dps']
                stats["raw_dps"] = dps
                stats["online"] = True
                
                # --- APPLYING VERIFIED DUAL-CLAMP MAPPINGS ---
                # Shared Voltage
                stats["voltage"] = dps.get('101', 0) / 10.0
                
                # Clamp 1 (Phase A)
                stats["clamp1_current"] = dps.get('102', 0) / 1000.0
                stats["clamp1_power"] = dps.get('103', 0)
                
                # Clamp 2 (Phase B)
                stats["clamp2_current"] = dps.get('110', 0) / 1000.0
                stats["clamp2_power"] = dps.get('111', 0)
                
                # Publish to MQTT
                if mqtt_c.is_connected():
                    # Send individual values for Home Assistant / Dashboards
                    mqtt_c.publish("tuya/energy/voltage", stats["voltage"])
                    mqtt_c.publish("tuya/energy/clamp1/power", stats["clamp1_power"])
                    mqtt_c.publish("tuya/energy/clamp1/current", stats["clamp1_current"])
                    mqtt_c.publish("tuya/energy/clamp2/power", stats["clamp2_power"])
                    mqtt_c.publish("tuya/energy/clamp2/current", stats["clamp2_current"])
                    # Send bulk JSON
                    mqtt_c.publish("tuya/energy/state", json.dumps(stats))
            else:
                stats["online"] = False
        except Exception as e:
            print(f"Polling Error: {e}")
            stats["online"] = False
        
        time.sleep(5)

# Background Thread
threading.Thread(target=tuya_worker, daemon=True).start()

@app.route('/')
def index():
    return render_template_string("""
    <body style="background:#0f172a; color:#f8fafc; font-family:sans-serif; padding: 30px;">
        <div style="max-width: 800px; margin: auto;">
            <header style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px;">
                <h1 style="color:#38bdf8; margin:0;">Dual-Clamp Monitor</h1>
                <span style="background:{{ '#22c55e' if stats.online else '#ef4444' }}; padding:5px 15px; border-radius:20px; font-weight:bold; font-size:0.8em;">
                    {{ 'ONLINE' if stats.online else 'OFFLINE' }}
                </span>
            </header>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                <div style="background:#1e293b; padding:25px; border-radius:15px; border-left: 5px solid #38bdf8;">
                    <h3 style="margin-top:0; color:#94a3b8;">Clamp 1</h3>
                    <div style="font-size:3em; font-weight:bold;">{{ stats.clamp1_power }}<span style="font-size:0.4em; color:#94a3b8; margin-left:5px;">W</span></div>
                    <div style="color:#94a3b8; margin-top:10px;">Current: {{ stats.clamp1_current }}A</div>
                </div>
                
                <div style="background:#1e293b; padding:25px; border-radius:15px; border-left: 5px solid #818cf8;">
                    <h3 style="margin-top:0; color:#94a3b8;">Clamp 2</h3>
                    <div style="font-size:3em; font-weight:bold;">{{ stats.clamp2_power }}<span style="font-size:0.4em; color:#94a3b8; margin-left:5px;">W</span></div>
                    <div style="color:#94a3b8; margin-top:10px;">Current: {{ stats.clamp2_current }}A</div>
                </div>
            </div>

            <div style="background:#1e293b; padding:20px; border-radius:15px; margin-bottom:30px;">
                <span style="color:#94a3b8;">Mains Voltage:</span> 
                <span style="font-size:1.5em; font-weight:bold; margin-left:10px;">{{ stats.voltage }}V</span>
            </div>

            <details>
                <summary style="cursor:pointer; color:#64748b; font-size:0.9em;">Show Raw Debug Data</summary>
                <pre style="background:#000; padding:15px; border-radius:10px; color:#4ade80; margin-top:10px; font-size:0.85em;">{{ stats.raw_dps | tojson(indent=2) }}</pre>
            </details>
        </div>
        <script>setTimeout(() => location.reload(), 5000);</script>
    </body>
    """, stats=stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
