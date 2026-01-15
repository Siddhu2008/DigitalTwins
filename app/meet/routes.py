import string
import random
from datetime import datetime
import jwt
from flask import render_template, redirect, url_for, jsonify, request, current_app, session
from app.meet import meet_bp
from app.db import mongo
from app.auth.utils import token_required
from app.meetings.persona_service import PersonaService
from app.meetings.services import process_meeting
import json

def generate_meeting_code():
    """Generates a Google Meet style code: abc-defg-hij"""
    p1 = ''.join(random.choices(string.ascii_lowercase, k=3))
    p2 = ''.join(random.choices(string.ascii_lowercase, k=4))
    p3 = ''.join(random.choices(string.ascii_lowercase, k=3))
    return f"{p1}-{p2}-{p3}"

@meet_bp.route('/create', methods=['POST'])
@token_required
def create_meeting(current_user):
    data = request.get_json(silent=True) or {}
    meeting_id = generate_meeting_code()
    
    # Extract metadata
    title = data.get('title', f"Meeting {meeting_id}")
    meeting_type = data.get('type', 'instant')
    user_id = str(current_user['_id'])

    # Store in Active Meetings (for signaling/room)
    mongo.db.active_meetings.insert_one({
        "_id": meeting_id,
        "created_at": datetime.utcnow(),
        "host_id": user_id,
        "title": title,
        "type": meeting_type
    })
    
    # Also save to User's Meetings list
    mongo.db.meetings.insert_one({
        "user_id": user_id,
        "title": title,
        "filename": meeting_id, 
        "created_at": datetime.utcnow(),
        "status": "scheduled" if meeting_type == 'later' else 'active',
        "meeting_id": meeting_id,
        "is_scheduled": meeting_type == 'later'
    })
    
    return jsonify({
        'meetingId': meeting_id, 
        'url': f'/meet/{meeting_id}',
        'title': title
    })

@meet_bp.route('/validate/<meeting_id>', methods=['GET'])
@token_required
def validate_meeting(current_user, meeting_id):
    exists = mongo.db.active_meetings.find_one({"_id": meeting_id})
    return jsonify({'valid': bool(exists)})

@meet_bp.route('/new')
def new_meeting():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # Instant meeting - create and redirect
    meeting_id = generate_meeting_code()
    mongo.db.active_meetings.insert_one({
        "_id": meeting_id,
        "created_at": datetime.utcnow(),
        "type": "instant"
    })
    return redirect(url_for('meet.meeting_room', meeting_id=meeting_id))



@meet_bp.route('/<meeting_id>/agenda', methods=['GET', 'POST'])
@token_required
def meeting_agenda(current_user, meeting_id):
    meeting = mongo.db.active_meetings.find_one({"_id": meeting_id})
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
        
    # Security: Only host can see/edit agenda
    print(f"DEBUG: Agenda check - host_id: {meeting['host_id']} (type: {type(meeting['host_id'])}), user_id: {current_user['_id']} (type: {type(current_user['_id'])})")
    if str(meeting['host_id']) != str(current_user['_id']):
        return jsonify({'error': 'Unauthorized'}), 403
        
    if request.method == 'POST':
        data = request.get_json()
        agenda = data.get('agenda', '')
        mongo.db.active_meetings.update_one(
            {"_id": meeting_id},
            {"$set": {"agenda": agenda}}
        )
        return jsonify({'success': True})
        
    return jsonify({'agenda': meeting.get('agenda', '')})

@meet_bp.route('/<meeting_id>')
def meeting_room(meeting_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # Verify existence
    meeting = mongo.db.active_meetings.find_one({"_id": meeting_id})
    if not meeting:
        return render_template('error.html', message="This meeting code is invalid or has expired."), 404
        
    currentUser = mongo.db.users.find_one({'_id': session['user_id']}) # Get full user for template if needed
    
    return render_template('meet/room.html', 
        meeting_id=meeting_id, 
        meeting=meeting,
        current_user_id=str(session['user_id'])
    )

@meet_bp.route('/<meeting_id>/transcripts', methods=['GET'])
@token_required
def get_transcripts(current_user, meeting_id):
    summary = mongo.db.transcripts.find({'meeting_id': meeting_id}).sort('timestamp', 1)
    transcripts = []
    for t in summary:
        transcripts.append({
            'speaker': t.get('speaker'),
            'text': t.get('text'),
            'timestamp': t.get('timestamp').isoformat()
        })
    return jsonify(transcripts)

@meet_bp.route('/<meeting_id>/end', methods=['POST'])
@token_required
def end_meeting(current_user, meeting_id):
    # Security: Only host can end meeting
    meeting = mongo.db.active_meetings.find_one({"_id": meeting_id})
    if not meeting:
        return jsonify({'error': 'Meeting not found'}), 404
        
    if str(meeting['host_id']) != str(current_user['_id']):
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Trigger AI processing
    # Collect all transcripts
    transcripts = list(mongo.db.transcripts.find({'meeting_id': meeting_id}).sort('timestamp', 1))
    transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in transcripts])
    
    # Save full transcript file for processing
    filename = f"transcript_{meeting_id}.txt"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    import os
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    with open(os.path.join(upload_folder, filename), "w", encoding='utf-8') as f:
        f.write(transcript_text)
        
    # Update meeting record with filename
    mongo.db.meetings.update_one(
        {'meeting_id': meeting_id},
        {'$set': {'filename': filename, 'status': 'ended', 'ended_at': datetime.utcnow()}}
    )
    
    # Process with Gemini
    # We need to find the specific meeting _id from meetings collection
    meeting_record = mongo.db.meetings.find_one({'meeting_id': meeting_id})
    if meeting_record:
        process_meeting(str(meeting_record['_id']))
        
    # Remove from active_meetings
    mongo.db.active_meetings.delete_one({'_id': meeting_id})
    
    return jsonify({'success': True})

@meet_bp.route('/<meeting_id>/delegate', methods=['POST'])
@token_required
def enable_delegate(current_user, meeting_id):
    data = request.get_json()
    enable = data.get('enable', True)
    
    mongo.db.active_meetings.update_one(
        {'_id': meeting_id},
        {'$set': {
            'ai_delegate_enabled': enable,
            'ai_delegate_user_id': str(current_user['_id'])
        }}
    )
    
    return jsonify({'success': True})
