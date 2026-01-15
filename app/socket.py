from flask_socketio import SocketIO, emit, join_room
from flask import request

socketio = SocketIO()

# State management
user_to_sid = {} # { user_id: sid }
rooms = {}       # { room_id: { sid: name } }

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('register_session')
def handle_register(data):
    user_id = data.get('user_id')
    if user_id:
        user_to_sid[user_id] = request.sid
        print(f"User {user_id} registered with sid {request.sid}")

# --- DIRECT CALLING ---
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
            'caller_sid': request.sid,
            'meeting_id': data.get('meeting_id')
        }, room=target_sid)
    else:
        emit('call_failed', {'message': 'User is offline'}, room=request.sid)

@socketio.on('accept_call')
def handle_accept(data):
    caller_sid = data.get('caller_sid')
    if caller_sid:
        emit('call_accepted', {
            'meeting_id': data.get('meeting_id')
        }, room=caller_sid)

@socketio.on('decline_call')
def handle_decline(data):
    caller_sid = data.get('caller_sid')
    if caller_sid:
        emit('call_declined', room=caller_sid)

# --- MEETING SIGNALING ---
@socketio.on('join_meeting')
def handle_join(data):
    meeting_id = data.get('meetingId')
    name = data.get('name')
    role = data.get('role', 'guest')
    if not meeting_id: return
    
    # Validate against DB
    from app.db import mongo
    if not mongo.db.active_meetings.find_one({"_id": meeting_id}):
        emit('error', {'message': 'Invalid meeting ID'}, room=request.sid)
        return
    
    join_room(meeting_id)
    if meeting_id not in rooms:
        rooms[meeting_id] = {}
    
    # Add user to room first
    rooms[meeting_id][request.sid] = {'name': name, 'role': role}
    
    print(f"DEBUG: Current rooms[meeting_id]: {rooms[meeting_id]}")
    
    # Send existing participants to new user
    participant_list = []
    for sid, n in rooms[meeting_id].items():
        if sid != request.sid:  # Exclude self from initial list
            p_name = n['name'] if isinstance(n, dict) else str(n)
            participant_list.append({'sid': sid, 'name': p_name})
        
    print(f"DEBUG: Sending room_info to {request.sid} with {len(participant_list)} participants")
    emit('room_info', {'users': participant_list}, room=request.sid)
    
    # Notify all users (including self) about new joiner
    print(f"DEBUG: Broadcasting user_joined for {name} ({request.sid}) to room {meeting_id}")
    emit('user_joined', {'sid': request.sid, 'name': name}, room=meeting_id)
    print(f"User {name} ({request.sid}) joined meeting {meeting_id} as {role}. Total users: {len(rooms[meeting_id])}")

@socketio.on('signal')
def handle_signal(data):
    to_sid = data.get('to')
    if to_sid:
        emit('signal', {
            'from': request.sid,
            'type': data.get('type'),
            'data': data.get('data')
        }, room=to_sid)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Remove from user_to_sid
    for uid, sid in list(user_to_sid.items()):
        if sid == request.sid:
            del user_to_sid[uid]
    
    # Remove from meeting rooms
    for rid, users in list(rooms.items()):
        if request.sid in users:
            name = users.pop(request.sid)
            emit('user_left', {'sid': request.sid}, room=rid)
            print(f"User {name} left meeting {rid}")
            
            if not users:
                # Last user left, update status to past
                from app.meetings.services import update_meeting_end_status
                update_meeting_end_status(rid)
                del rooms[rid]

@socketio.on('send_chat')
def handle_chat(data):
    meeting_id = data.get('meetingId')
    sender_name = rooms.get(meeting_id, {}).get(request.sid, {}).get('name', 'Unknown')
    message_data = {
        'sid': request.sid,
        'from': sender_name,
        'message': data.get('message')
    }
    # Emit to ALL users including sender
    emit('chat_message', message_data, room=meeting_id)
    print(f"Chat from {sender_name} in {meeting_id}: {data.get('message')}")

@socketio.on('reaction')
def handle_reaction(data):
    for rid, users in rooms.items():
        if request.sid in users:
            emit('reaction', {'emoji': data.get('emoji'), 'sid': request.sid}, room=rid)
            break

@socketio.on('raise_hand')
def handle_hand():
    for rid, users in rooms.items():
        if request.sid in users:
            emit('hand_raised', {'name': users[request.sid]['name'], 'sid': request.sid}, room=rid)
            break

@socketio.on('caption_broadcast')
def handle_caption(data):
    for rid, users in rooms.items():
        if request.sid in users:
            emit('caption_broadcast', {'from': users[request.sid]['name'], 'text': data.get('text')}, room=rid, include_self=False)
            break
