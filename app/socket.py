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
    
    # Notify others and send room info to joiner
    participant_list = []
    for sid, n in rooms[meeting_id].items():
        p_name = n['name'] if isinstance(n, dict) else str(n)
        participant_list.append({'sid': sid, 'name': p_name})
        
    emit('room_info', {'users': participant_list}, room=request.sid)
    rooms[meeting_id][request.sid] = {'name': name, 'role': role}
    emit('user_joined', {'sid': request.sid, 'name': name}, room=meeting_id, include_self=False)
    print(f"User {name} ({request.sid}) joined meeting {meeting_id} as {role}")

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
    emit('chat_message', {
        'sid': request.sid,
        'from': rooms.get(meeting_id, {}).get(request.sid, {}).get('name', 'Unknown'),
        'message': data.get('message')
    }, room=meeting_id)

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
