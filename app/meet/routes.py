import string
import random
from datetime import datetime
import jwt
from flask import render_template, redirect, url_for, jsonify, request, current_app, session
from app.meet import meet_bp
from app.db import mongo
from app.auth.utils import token_required

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

@meet_bp.route('/<meeting_id>')
def meeting_room(meeting_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # Verify existence
    exists = mongo.db.active_meetings.find_one({"_id": meeting_id})
    if not exists:
        return render_template('error.html', message="This meeting code is invalid or has expired."), 404
        
    return render_template('meet/room.html', meeting_id=meeting_id)
