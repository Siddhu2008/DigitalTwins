from app.db import mongo
from bson.objectid import ObjectId

def get_tone_profile(user_id):
    profile = mongo.db.tone_profiles.find_one({'user_id': user_id})
    if not profile:
        return {
            'formality': 50, # 0-100
            'empathy': 50,
            'verbosity': 50,
            'style': 'Neutral'
        }
    return profile

def analyze_text_sample(user_id, text_sample):
    # Mock Analysis Logic
    length = len(text_sample)
    formality = 80 if 'sincerely' in text_sample.lower() else 40
    empathy = 70 if 'thank' in text_sample.lower() else 30
    
    profile = {
        'user_id': user_id,
        'formality': formality,
        'empathy': empathy,
        'verbosity': min(100, length // 10),
        'style': 'Professional' if formality > 60 else 'Casual'
    }
    
    mongo.db.tone_profiles.update_one(
        {'user_id': user_id},
        {'$set': profile},
        upsert=True
    )
    return profile
