import network
import socket
import time
import machine
import ujson
import urequests
from paper_fetcher import PaperFetcher
from web_server import WebServer
from config_file import WIFI_SSID, WIFI_PASSWORD, CHECK_INTERVAL, KEYWORDS, MAX_PAPERS
import os

led = machine.Pin("LED", machine.Pin.OUT)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print("Available networks:")
    for network_ssid in wlan.scan():
        print(network_ssid[0].decode(), end=", ")
    print()
    
    print(f"Connecting to network \"{WIFI_SSID}\"...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait = 30
    while max_wait > 0:
        status = wlan.status()
        print(f"Status: {status}")
        
        if status < 0 or status >= 3:
            break
        max_wait -= 1
        print("Waiting for connection...")
        time.sleep(2)
    
    if wlan.status() == 2:
        raise RuntimeError("Connection failed: Wrong password")
    elif wlan.status() == -1:
        raise RuntimeError("Connection failed: No access point found")
    elif wlan.status() == -2:
        raise RuntimeError("Connection failed: Network error")
    elif wlan.status() != 3:
        raise RuntimeError(f"Connection failed: Unknown error (status {wlan.status()})")
    
    status = wlan.ifconfig()
    print(f"Connected to WiFi. IP: {status[0]}")
    return wlan

# Main function
def main():
    try:
        wlan = connect_wifi()
        
        keywords = KEYWORDS
        paper_fetcher = PaperFetcher(keywords, MAX_PAPERS)
        
        web_server = WebServer(port=80)
        
        last_check_time = 0
        
        while True:
            current_time = time.time()
            
            if current_time - last_check_time >= CHECK_INTERVAL:
                led.on()
                print("Checking for new papers...")
                
                try:
                    new_papers = paper_fetcher.fetch_papers()
                    if new_papers:
                        print(f"Found {len(new_papers)} new papers")
                        paper_fetcher.save_papers(new_papers)
                    else:
                        print("No new papers found")
                except Exception as e:
                    print(f"Error fetching papers: {e}")
                
                last_check_time = current_time
                led.off()
            
            web_server.handle_requests(paper_fetcher.get_papers())
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Program stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(10)
        machine.reset()

if __name__ == "__main__":
    #os.remove("papers/papers.json")
    main()