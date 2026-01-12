from flask import render_template, redirect, url_for, jsonify, request
from app.meet import meet_bp
from app.db import mongo
import random
import string
from datetime import datetime

def generate_meeting_code():
    """Generates a Google Meet style code: abc-defg-hij"""
    p1 = ''.join(random.choices(string.ascii_lowercase, k=3))
    p2 = ''.join(random.choices(string.ascii_lowercase, k=4))
    p3 = ''.join(random.choices(string.ascii_lowercase, k=3))
    return f"{p1}-{p2}-{p3}"

@meet_bp.route('/create', methods=['POST'])
def create_meeting():
    data = request.get_json(silent=True) or {}
    meeting_id = generate_meeting_code()
    
    # Store in DB
    mongo.db.active_meetings.insert_one({
        "_id": meeting_id,
        "created_at": datetime.utcnow(),
        "host_id": data.get('host_id'),
        "type": data.get('type', 'instant')
    })
    
    return jsonify({'meetingId': meeting_id, 'url': f'/meet/{meeting_id}'})

@meet_bp.route('/validate/<meeting_id>', methods=['GET'])
def validate_meeting(meeting_id):
    exists = mongo.db.active_meetings.find_one({"_id": meeting_id})
    return jsonify({'valid': bool(exists)})

@meet_bp.route('/new')
def new_meeting():
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
    # Verify existence
    exists = mongo.db.active_meetings.find_one({"_id": meeting_id})
    if not exists:
        return render_template('error.html', message="This meeting code is invalid or has expired."), 404
        
    return render_template('meet/room.html', meeting_id=meeting_id)
