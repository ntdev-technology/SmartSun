"""
(C) NTDEV 2023-2024, all rights reserved.

"""
from flask import Flask
from SmartSunController.SmartSunCore.Misc import EthernetInfo
import time
from app import app as flask_app
app = flask_app.wsgi_app

if __name__ == '__main__':
    chkETHER = EthernetInfo()
    while not chkETHER.CheckInternetAvailability():
        print("Waiting for internet...")
        time.sleep(1)
    try:
        app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False)
    except Exception as e:
        print("ERROR: {0}".format(e))
        exit()