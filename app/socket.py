from flask_socketio import SocketIO, emit, join_room
from flask import request

socketio = SocketIO()

# Map user_id to session IDs
user_to_sid = {}

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('register_session')
def handle_register(data):
    user_id = data.get('user_id')
    if user_id:
        user_to_sid[user_id] = request.sid
        print(f"User {user_id} registered with sid {request.sid}")

@socketio.on('initiate_call')
def handle_call(data):
    target_user_id = data.get('target_user_id')
    caller_name = data.get('caller_name')
    caller_id = data.get('caller_id')
    
    target_sid = user_to_sid.get(target_user_id)
    if target_sid:
        emit('receiving_call', {
            'caller_id': caller_id,
            'caller_name': caller_name,
            'meeting_id': data.get('meeting_id')
        }, room=target_sid)
    else:
        emit('call_failed', {'message': 'User is offline'}, room=request.sid)

@socketio.on('accept_call')
def handle_accept(data):
    caller_id = data.get('caller_id')
    caller_sid = user_to_sid.get(caller_id)
    if caller_sid:
        emit('call_accepted', {
            'meeting_id': data.get('meeting_id')
        }, room=caller_sid)

@socketio.on('decline_call')
def handle_decline(data):
    caller_id = data.get('caller_id')
    caller_sid = user_to_sid.get(caller_id)
    if caller_sid:
        emit('call_declined', room=caller_sid)
