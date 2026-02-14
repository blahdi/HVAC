import os
import time
import json
import paho.mqtt.client as mqtt
import tinytuya
from dotenv import load_dotenv

load_dotenv()

# Configuration
DEVICE_ID = os.getenv("DEVICE_ID")
IP_ADDRESS = os.getenv("IP_ADDRESS")
LOCAL_KEY = os.getenv("LOCAL_KEY")
MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")

d = tinytuya.OutletDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
d.set_version(3.4) 

mqtt_c = mqtt.Client()
if MQTT_USER and MQTT_PASS:
    mqtt_c.username_pw_set(MQTT_USER, MQTT_PASS)

def send_discovery():
    sensors = [
        ("clamp1_power", "W", "power", "measurement", "HVAC Clamp 1 Power", "tuya/energy/clamp1_power"),
        ("clamp1_current", "A", "current", "measurement", "HVAC Clamp 1 Current", "tuya/energy/clamp1_current"),
        ("clamp2_power", "W", "power", "measurement", "HVAC Clamp 2 Power", "tuya/energy/clamp2_power"),
        ("clamp2_current", "A", "current", "measurement", "HVAC Clamp 2 Current", "tuya/energy/clamp2_current"),
        ("voltage", "V", "voltage", "measurement", "HVAC Voltage", "tuya/energy/voltage"),
        ("total_energy", "kWh", "energy", "total_increasing", "HVAC Total Energy", "tuya/energy/total_energy"),
    ]

    for sensor_id, unit, dev_class, state_class, friendly_name, topic in sensors:
        discovery_topic = f"homeassistant/sensor/hvac_{sensor_id}/config"
        payload = {
            "name": friendly_name,
            "stat_t": topic,
            "unit_of_meas": unit,
            "dev_cla": dev_class,
            "stat_cla": state_class,
            "uniq_id": f"hvac_{sensor_id}",
            "dev": {
                "ids": ["hvac_monitor_tuya"],
                "name": "HVAC Energy Monitor",
                "mf": "Tuya",
                "mdl": "Dual Clamp Meter"
            }
        }
        mqtt_c.publish(discovery_topic, json.dumps(payload), retain=True)

    # --- SPECIFIC CHANGE: ADD HVAC ACTIVITY BINARY SENSOR ---
    binary_discovery_topic = "homeassistant/binary_sensor/hvac_activity/config"
    binary_payload = {
        "name": "HVAC Activity Status",
        "stat_t": "tuya/energy/hvac_active",
        "payload_on": "ON",
        "payload_off": "OFF",
        "dev_cla": "running",
        "uniq_id": "hvac_activity_status",
        "dev": {"ids": ["hvac_monitor_tuya"]}
    }
    mqtt_c.publish(binary_discovery_topic, json.dumps(binary_payload), retain=True)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        send_discovery()

mqtt_c.on_connect = on_connect
mqtt_c.connect(MQTT_HOST, MQTT_PORT, 60)
mqtt_c.loop_start()

print("Starting Bridge Loop...")

while True:
    try:
        data = d.status()
        if 'dps' in data:
            dps = data['dps']
            
            # Final Mapping based on raw DPS diagnostics
            stats = {
                "voltage": dps.get('104', 0) / 10,           # ID 104: Voltage
                "clamp2_power": dps.get('103', 0) / 10,     # ID 103: Clamp 2 Watts
                "clamp2_current": dps.get('102', 0) / 1000, # ID 102: Clamp 2 Amps
                "clamp1_power": dps.get('101', 0) / 10,     # ID 101: Clamp 1 Watts
                "clamp1_current": dps.get('18', 0) / 1000,  # ID 18: Likely Clamp 1 Amps
                "total_energy": dps.get('17', 0) / 100      # ID 17: Total Energy kWh
            }

            for key, value in stats.items():
                mqtt_c.publish(f"tuya/energy/{key}", value)
            
            # --- SPECIFIC CHANGE: LOGIC FOR ON/OFF STATUS ---
            total_power = stats["clamp1_power"] + stats["clamp2_power"]
            hvac_active = "ON" if total_power > 50 else "OFF"
            mqtt_c.publish("tuya/energy/hvac_active", hvac_active)
            
            print(f"Sent to HA: {stats} | HVAC Active: {hvac_active}")
        else:
            print("Device busy or offline...")
            
    except Exception as e:
        print(f"Bridge Error: {e}")
        
    time.sleep(10)
