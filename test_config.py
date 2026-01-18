
import os
from flask import Flask
from config import Config
from app.db import mongo
import certifi

def test_config():
    # Simulate Render environment where .env is not loaded by dotenv (if we don't call load_dotenv)
    # But wait, run.py calls load_dotenv().
    
    # Let's inspect what Config.MONGO_URI is resolving to
    print(f"Config.MONGO_URI raw: {Config.MONGO_URI}")
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    print(f"app.config['MONGO_URI']: {app.config.get('MONGO_URI')}")
    
    # manually init mongo to see what it does
    try:
        mongo.init_app(app, tlsCAFile=certifi.where())
        print(f"Mongo URI after init: {app.config.get('MONGO_URI')}")
        # In newer flask-pymongo, how do we check the uri?
        # It's usually stored in app.extensions['pymongo'] ...
    except Exception as e:
        print(f"Error init app: {e}")

if __name__ == "__main__":
    test_config()
