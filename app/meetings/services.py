import os
from app.db import mongo
from datetime import datetime
from bson.objectid import ObjectId

def save_meeting_metadata(user_id, title, filename):
    meeting = {
        'user_id': user_id,
        'title': title,
        'filename': filename,
        'created_at': datetime.utcnow(),
        'status': 'processing'
    }
    result = mongo.db.meetings.insert_one(meeting)
    return str(result.inserted_id)

def get_meeting_by_id(meeting_id):
    return mongo.db.meetings.find_one({'_id': ObjectId(meeting_id)})

def get_user_meetings(user_id):
    return list(mongo.db.meetings.find({'user_id': user_id}).sort('created_at', -1))

def mock_process_meeting(meeting_id):
    # Simulate AI processing
    summary = {
        'meeting_id': meeting_id,
        'summary_text': "This was a productive meeting discussing the project roadmap. Key decisions were made regarding the tech stack and timeline.",
        'key_points': [
            "Use Flask for backend",
            "Use Tailwind for frontend",
            "MVP deadline is in 2 weeks"
        ],
        'action_items': [
            "Setup repo",
            "Design database schema",
            "Create initial UI mockups"
        ]
    }
    
    mongo.db.summaries.insert_one(summary)
    mongo.db.meetings.update_one(
        {'_id': ObjectId(meeting_id)},
        {'$set': {'status': 'completed'}}
    )
    return summary

def get_summary_by_meeting_id(meeting_id):
    return mongo.db.summaries.find_one({'meeting_id': meeting_id})
