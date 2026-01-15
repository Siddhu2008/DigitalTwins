import os
import sys
from dotenv import load_dotenv
import certifi

load_dotenv()

print("--- Testing Imports ---")
try:
    import google.generativeai as genai
    print("SUCCESS: google.generativeai imported")
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        print("SUCCESS: Gemini configured")
    except Exception as e:
        print(f"FAILURE: Gemini configuration failed: {e}")

except ImportError as e:
    print(f"FAILURE: google.generativeai import failed: {e}")

print("\n--- Testing MongoDB Connection ---")
try:
    from pymongo import MongoClient
    uri = os.environ.get('MONGO_URI')
    print(f"URI: {uri.split('@')[1] if '@' in uri else 'Wait, invalid URI format for logging'}") 
    
    # Test 1: Standard Connection
    print("Attempting connection with certifi...")
    client = MongoClient(uri, tlsCAFile=certifi.where())
    # Force a call to check connection
    client.admin.command('ping')
    print("SUCCESS: MongoDB Connected with certifi!")
    
except Exception as e:
    print(f"FAILURE: MongoDB Connection failed: {e}")

print("\n--- Testing Eventlet DNS Interaction (Simulation) ---")
try:
    import eventlet
    print("Eventlet imported. Note: Monkey patch not applied in this script yet.")
except ImportError:
    print("Eventlet not installed.")
