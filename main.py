import network
import time
import urequests
from machine import Pin, SoftI2C
import ssd1306
import ntptime
import gc

# --- Display on OLED ---
i2c = SoftI2C(scl=Pin(25), sda=Pin(26))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(0.5)
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
    year = int(iso_str[0:4])
    month = int(iso_str[5:7])
    day = int(iso_str[8:10])
    hour = int(iso_str[11:13])
    minute = int(iso_str[14:16])
    second = int(iso_str[17:19])
    return time.mktime((year, month, day, hour, minute, second, 0, 0))

# --- Setup Wi-Fi and Time ---
WIFI_SSID = "YOUR_WIFI_NAME_HERE"
WIFI_PASS = "YOUR_WIFI_PASSWORD_HERE"

connect_wifi(WIFI_SSID, WIFI_PASS)
sync_time() # IMPORTANT: Actually call the sync function!

url ='https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival?BusStopCode=52211&ServiceNo=230'

headers = {
    "AccountKey": "YOUR_LTA_PASSKEY_HERE", 
    "accept": "application/json"
}

# --- Fetch API Data ---
gc.collect() # Prevent memory crashes
response = urequests.get(url, headers=headers)
data = response.json()
response.close()
tsugi = [data["Services"][0]["NextBus"]['EstimatedArrival'], data["Services"][0]["NextBus2"]['EstimatedArrival'], data["Services"][0]["NextBus3"]['EstimatedArrival']]
    
display_var = []
    
# Singapore is UTC+8. ntptime sets UTC. Add 8 hours (28800 seconds).
now_sgt = time.time() + 28800 

for element in tsugi:
    if element:
        dt = parse_iso_to_epoch(element)
        diff = int((dt - now_sgt) // 60)
        if diff <= 0:
            display_var.append("Ar")
        else:
            display_var.append(str(diff))
    
# --- Display on OLED ---
i2c = SoftI2C(scl=Pin(25), sda=Pin(26))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.text("Lighthouse Sch", 0, 0)
oled.text(f"230: {display_var[0]},{display_var[1]},{display_var[2]}", 0, 16)

oled.show()

print("Done rendering to OLED.")