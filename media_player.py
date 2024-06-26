import webview
import os
import time
import sys
import threading
import paho.mqtt.client as mqtt
import logging
import json
import uuid
import requests
import configparser
import utils
import urllib.request
from protocol import MessageProtocol
from scheduler import Scheduler
import web_server
import threading
import network_manager
from mqtt_client import MQTTClient

CONFIG_FILE = "config.ini"
DEFAULT_CONFIG_FILE = "default_config.ini"
UUID_FILE = "uuid"

def setup():

    while not os.path.exists(CONFIG_FILE) or not os.path.exists(UUID_FILE):
        time.sleep(1)

    # load config
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # setup logging
    logging.basicConfig(level=config["Logging"]["log_level"], format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=config["Logging"]["log_file"])
    mqtt_logger = logging.getLogger("MQTTClient")
    scheduler_logger = logging.getLogger("Scheduler")
    logging.getLogger('werkzeug').disabled = True
    logging.getLogger('urllib3.connectionpool').disabled = True
    
    if os.path.isfile("static/current.html"):
        window.load_url(utils.get_full_path("static/current.html"))
    else:
        window.load_url(utils.get_full_path(config["MediaPlayer"]["default_template"]))

    # start the scheduler main loop
    scheduler = Scheduler(scheduler_logger, config, window)
    scheduler_thread = threading.Thread(target=scheduler.main_loop)
    scheduler_thread.start()

    # create an instante of the mqtt client and start the loop
    mqtt_client = MQTTClient(mqtt_logger, config, scheduler)
    mqtt_client.start()
    
        
if __name__ == '__main__':

    # load default config
    default_config = configparser.ConfigParser()
    default_config.read(DEFAULT_CONFIG_FILE)
    
    networks = network_manager.get_networks()
    flask_thread = threading.Thread(target=web_server.run, daemon=True, args=(networks,))
    flask_thread.start()

    if not os.path.isfile(CONFIG_FILE):

        ssid = "DetiSignage-" + str(uuid.uuid4())[:8]
        password = str(uuid.uuid4())[:8]
        network_manager.create_hotspot(ssid,password)
        
        utils.generate_wifi_qrcode(ssid, password, target="static/qr_code.png")
        
        url = "http://10.42.0.1:5000/config"

        html = utils.render_jinja_html("templates", "setup.html", ssid=ssid, password=password, url=url)
        utils.store_static("setup.html", html)
        
        window = webview.create_window('MediaPlayer', "static/setup.html", fullscreen=True)
    
    else:
        window = webview.create_window('MediaPlayer', default_config["MediaPlayer"]["default_template"], fullscreen=True, confirm_close=False)

    webview.start(func=setup)
