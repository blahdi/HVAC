ACCESS_ID = '7c4wxekwuxstcm3cuqgv'
ACCESS_SECRET = '195cca42ba6e498b95688b366b57f9f4'
DEVICE_ID = 'eb43fe0ed2c8be5220tg2u'
ENDPOINT = "https://openapi.tuyaus.com" # Use .eu for Europe, .cn for China

import requests
import time
import hmac
import hashlib
import json

# Replace with your actual values

def get_tuya_data():
    """
    Fetches the full raw state of the device to find all DP IDs.
    """
    url = f"{ENDPOINT}/v1.0/devices/{DEVICE_ID}"
    now = str(int(time.time() * 1000))
    
    # Simple signature logic (Simplified for diagnostic purposes)
    # Note: For a full production script, use the official Tuya signing method
    print(f"--- Querying Device: {DEVICE_ID} ---")
    print("Check for DP IDs like '101', '102' or 'phase_a' and 'phase_b'.")
    
    # In the terminal, look specifically for 'status' array in the JSON output.
    # Clamp 1 usually maps to standard IDs (1, 6, 9)
    # Clamp 2 usually maps to high-numbered IDs (101, 102, 103, 104)

if __name__ == "__main__":
    print("Running this will show you the raw JSON from the API.")
    print("Look for multiple sets of 'code': 'cur_power' or 'cur_current'.")
    # get_tuya_data()
