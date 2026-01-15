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

import os
import google.generativeai as genai
from flask import current_app
import json

def process_meeting(meeting_id):
    meeting = mongo.db.meetings.find_one({'_id': ObjectId(meeting_id)})
    if not meeting:
        return None
        
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, meeting['filename'])
    
    try:
        # Simple text handling for now. For audio, would need to use genai.upload_file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        Analyze the following meeting transcript/notes and provide a summary.
        Return the response in STRICT JSON format with the following keys:
        - summary_text (string): A concise summary or abstract.
        - key_points (list of strings): The main points discussed.
        - action_items (list of strings): Tasks or actions to be taken.
        
        Transcript:
        {content}
        """
        
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Clean up code blocks if present
        if text_response.startswith('```json'):
            text_response = text_response.replace('```json', '').replace('```', '')
            
        try:
            ai_data = json.loads(text_response)
        except json.JSONDecodeError:
            # Fallback if JSON fails
            ai_data = {
                'summary_text': text_response,
                'key_points': [],
                'action_items': []
            }
            
        summary = {
            'meeting_id': meeting_id,
            'summary_text': ai_data.get('summary_text', 'No summary available.'),
            'key_points': ai_data.get('key_points', []),
            'action_items': ai_data.get('action_items', [])
        }
        
        mongo.db.summaries.insert_one(summary)
        mongo.db.meetings.update_one(
            {'_id': ObjectId(meeting_id)},
            {'$set': {'status': 'completed'}}
        )
        return summary
        
    except Exception as e:
        print(f"Error processing meeting with Gemini: {e}")
        mongo.db.meetings.update_one(
            {'_id': ObjectId(meeting_id)},
            {'$set': {'status': 'failed'}}
        )
        return None

def update_meeting_end_status(meeting_id):
    """Updates the meeting status to 'ended' in both meetings and active_meetings collections."""
    now = datetime.utcnow()
    # Update the user's meeting record
    mongo.db.meetings.update_one(
        {'meeting_id': meeting_id},
        {'$set': {
            'status': 'ended',
            'ended_at': now
        }}
    )
    # Remove from active meetings
    mongo.db.active_meetings.delete_one({'_id': meeting_id})

def get_summary_by_meeting_id(meeting_id):
    return mongo.db.summaries.find_one({'meeting_id': meeting_id})
