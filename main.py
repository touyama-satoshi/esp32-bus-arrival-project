import network
import time
import urequests
from machine import Pin, SoftI2C
import ssd1306
import ntptime
import gc

# --- Configuration ---
WIFI_SSID = ""
WIFI_PASS = ""
ACCOUNT_KEY = ""
URL = 'https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival?BusStopCode=52211&ServiceNo=230'

# --- Setup OLED Display ---
i2c = SoftI2C(scl=Pin(25), sda=Pin(26))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"Connecting to {ssid}...")
        wlan.connect(ssid, password)
        
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="")
        print()

    if wlan.isconnected():
        print("Connected successfully!")
        return True
    else:
        print("Failed to connect.")
        return False

def sync_time():
    ntptime.host = "time.google.com"
    for attempt in range(5):
        try:
            print(f"NTP sync attempt {attempt + 1}...")
            ntptime.settime()
            print("Time synced successfully!")
            return True
        except Exception as e:
            print("NTP attempt failed:", e)
            time.sleep(1)
    return False

def parse_iso_to_epoch(iso_str):
    if not iso_str:
        return None
    year, month, day = int(iso_str[0:4]), int(iso_str[5:7]), int(iso_str[8:10])
    hour, minute, second = int(iso_str[11:13]), int(iso_str[14:16]), int(iso_str[17:19])
    return time.mktime((year, month, day, hour, minute, second, 0, 0))

# --- Connect & Sync ---
connect_wifi(WIFI_SSID, WIFI_PASS)
sync_time()

# --- Fetch API Data ---
gc.collect() # Prevent memory crashes
headers = {
    "AccountKey": ACCOUNT_KEY, 
    "accept": "application/json"
}

response = urequests.get(URL, headers=headers)
data = response.json()
response.close()

# --- Process Bus Timings ---
display_var = []
now_sgt = time.time() + 28800  # SG time adjustment

# Check safely if 'Services' list actually contains data
if data.get("Services"):
    service = data["Services"][0]
    
    # Check all three potential buses safely
    for bus_key in ["NextBus", "NextBus2", "NextBus3"]:
        est = service.get(bus_key, {}).get("EstimatedArrival", "")
        
        if est:
            dt = parse_iso_to_epoch(est)
            diff = int((dt - now_sgt) // 60)
            if diff <= 0:
                display_var.append("Ar")
            else:
                display_var.append(str(diff))

# Join timings cleanly (e.g. "Ar, 5, 12" or "Ar, 5" or "No bus")
timings_str = ", ".join(display_var) if display_var else "No bus"

# --- Display on OLED ---
oled.fill(0)
oled.text("Lighthouse Sch", 0, 0)
oled.text(f"230: {timings_str}", 0, 16)
oled.show()

print("Done rendering to OLED.")
