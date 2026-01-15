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
    from app.db import mongo
    from datetime import datetime
    
    room_id = None
    for rid, users in rooms.items():
        if request.sid in users:
            room_id = rid
            break
            
    print(f"DEBUG: caption_broadcast received from {request.sid} in room {room_id}")
    if room_id:
        speaker_name = rooms[room_id][request.sid]['name']
        text = data.get('text')
        print(f"DEBUG: Speaker: {speaker_name}, Text: {text}")
        
        # 1. Save Transcript
        try:
            mongo.db.transcripts.insert_one({
                'meeting_id': room_id,
                'speaker': speaker_name,
                'text': text,
                'timestamp': datetime.utcnow()
            })
            print(f"DEBUG: Transcript saved to DB")
        except Exception as e:
            print(f"DEBUG: Failed to save transcript: {e}")
        
        emit('caption_broadcast', {'from': speaker_name, 'text': text}, room=room_id, include_self=False)
        
        # 2. AI Delegate Logic
        if 'ai_delegates' in rooms[room_id]:
            print(f"DEBUG: Checking {len(rooms[room_id]['ai_delegates'])} AI delegates")
            for delegate_user in rooms[room_id]['ai_delegates']:
                print(f"DEBUG: Comparing '{delegate_user['name'].lower()}' with '{text.lower()}'")
                if delegate_user['name'].lower() in text.lower() or "you" in text.lower():
                    # Only trigger if the speaker is NOT the delegate themselves
                    if speaker_name != delegate_user['name']:
                        print(f"DEBUG: AI Delegate trigger matched for {delegate_user['name']}")
                        process_ai_delegate_response(room_id, delegate_user, text, speaker_name)

def process_ai_delegate_response(meeting_id, delegate, context_text, speaker_name):
    """
    Delegate: {name, style, user_id}
    """
    import google.generativeai as genai
    import os
    from app.meetings.persona_service import PersonaService
    
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Get personalized prompt
        persona_service = PersonaService()
        user_id = delegate.get('user_id')
        system_prompt = None
        if user_id:
             system_prompt = persona_service.get_system_prompt(user_id)
             
        if not system_prompt:
             # Fallback default
             system_prompt = f"""
             You are acting as a digital twin for {delegate['name']}.
             Your speaking style is: {delegate.get('style', 'professional')}.
             """
        
        prompt = f"""
        {system_prompt}
        
        Context from meeting: 
        Speaker ({speaker_name}) said: "{context_text}"
        
        Respond briefly (under 2 sentences) as if you are {delegate['name']} attending the meeting.
        """
        
        response = model.generate_content(prompt)
        reply = response.text
        
        # Emit as a special chat message
        socketio.emit('chat_message', {
            'sid': 'AI_DELEGATE',
            'from': f"{delegate['name']} (AI)",
            'message': reply,
            'is_ai': True
        }, room=meeting_id)
        
    except Exception as e:
        print(f"AI Delegate Error: {e}")

@socketio.on('request_transcripts')
def handle_request_transcripts(data):
    meeting_id = data.get('meetingId')
    from app.db import mongo
    
    # Get all past transcripts
    cursor = mongo.db.transcripts.find({'meeting_id': meeting_id}).sort('timestamp', 1)
    history = []
    for t in cursor:
        history.append({
            'from': t.get('speaker'),
            'text': t.get('text'),
            'timestamp': t.get('timestamp').isoformat()
        })
    emit('transcript_history', {'history': history}, room=request.sid)

@socketio.on('enable_ai_delegate')
def handle_enable_ai_delegate(data):
    # data: { meetingId, name, style, userId }
    meeting_id = data.get('meetingId')
    if meeting_id in rooms:
        if 'ai_delegates' not in rooms[meeting_id]:
            rooms[meeting_id]['ai_delegates'] = []
            
        # Add to delegates if not exists
        exists = any(d['name'] == data['name'] for d in rooms[meeting_id]['ai_delegates'])
        if not exists:
            rooms[meeting_id]['ai_delegates'].append({
                'name': data.get('name'),
                'style': data.get('style', 'helpful and concise'),
                'user_id': data.get('userId')  # Store user_id for persona lookup
            })
            emit('chat_message', {
                'sid': 'SYSTEM',
                'from': 'System',
                'message': f"AI Delegate enabled for {data.get('name')}"
            }, room=meeting_id)

@socketio.on('chat_with_avatar')
def handle_avatar_chat(data):
    import google.generativeai as genai
    import os
    
    user_message = data.get('message')
    if not user_message:
        return
        
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Simple prompt for helpful assistant
        chat = model.start_chat(history=[])
        response = chat.send_message(user_message)
        
        emit('avatar_response', {'message': response.text})
    except Exception as e:
        print(f"Avatar Chat Error: {e}")
        emit('avatar_response', {'message': "I'm having trouble connecting to my brain right now. Please try again later."})
