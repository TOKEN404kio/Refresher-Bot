import time
import urllib.request
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is online and tracking active traffic!"

def run_server():
    # Runs the mini web server
    app.run(host='0.0.0.0', port=8080)

def self_ping_loop():
    # Wait for the server to boot up initially
    time.sleep(30)
    while True:
        try:
            # Looks for the custom URL Render assigned to you
            import os
            render_url = os.environ.get('RENDER_EXTERNAL_URL')
            if render_url:
                # Forces a fake web page load to reset Render's sleep countdown
                urllib.request.urlopen(render_url)
                print("Self-ping successful: Sleep timer reset.")
            else:
                print("Self-ping warning: 'RENDER_EXTERNAL_URL' variable not detected.")
        except Exception as e:
            print(f"Self-ping failed (Normal during cold start): {e}")
        
        # Pings itself every 5 minutes (300 seconds)
        time.sleep(300)

def keep_alive():
    # Starts the web server thread
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Starts the anti-sleep trick loop thread
    ping_thread = Thread(target=self_ping_loop)
    ping_thread.daemon = True
    ping_thread.start()
