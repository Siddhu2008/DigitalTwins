from dotenv import load_dotenv
import os

load_dotenv()

from app import create_app
from app.socket import socketio

app = create_app()

if __name__ == '__main__':
    # Disable debug mode to prevent auto-reload issues during login/signup
    # Use use_reloader=False to prevent multiple process spawning with Socket.IO
    socketio.run(app, debug=False, use_reloader=False, host='127.0.0.1', port=5000)
