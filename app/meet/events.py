from app.socket import socketio
from flask_socketio import emit, join_room, leave_room
from flask import request

# Store meeting states
# meetings = { meeting_id: { sid: { name: "User", role: "host" } } }
meetings = {}

@socketio.on('join_meeting')
def handle_join(data):
    meeting_id = data['meetingId']
    name = data['name']
    role = data.get('role', 'guest')
    sid = request.sid
    
    # 1. Validate against DB
    from app.db import mongo
    if not mongo.db.active_meetings.find_one({"_id": meeting_id}):
        emit('error', {'message': 'Invalid meeting ID'}, room=sid)
        return

    join_room(meeting_id)
    
    if meeting_id not in meetings:
        meetings[meeting_id] = {}
    
    # Store user info
    meetings[meeting_id][sid] = {'name': name, 'role': role}
    
    # Notify others in room
    existing_users = [
        {'sid': user_sid, 'name': user['name']} 
        for user_sid, user in meetings[meeting_id].items() 
        if user_sid != sid
    ]
    
    # Tell newcomer who is already there
    emit('room_info', {'users': existing_users}, room=sid)
    
    # Tell everyone else a new user joined
    emit('user_joined', {'sid': sid, 'name': name}, room=meeting_id, include_self=False)

@socketio.on('signal')
def handle_signal(data):
    target_sid = data['to']
    emit('signal', {
        'type': data['type'],
        'data': data['data'],
        'from': request.sid
    }, room=target_sid)

@socketio.on('send_chat')
def handle_chat(data):
    meeting_id = data['meetingId']
    msg = data['message']
    name = meetings.get(meeting_id, {}).get(request.sid, {}).get('name', 'Unknown')
    
    emit('chat_message', {
        'from': name,
        'message': msg,
        'sid': request.sid
    }, room=meeting_id)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    for mid, users in meetings.items():
        if sid in users:
            del users[sid]
            emit('user_left', {'sid': sid}, room=mid)
            if not users:
                del meetings[mid]
            break
