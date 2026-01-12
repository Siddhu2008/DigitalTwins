from app.db import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import datetime


def create_user(email, password, name, role='professional', tone='formal'):
    existing_user = mongo.db.users.find_one({'email': email})
    if existing_user:
        return None
    
    hashed_password = generate_password_hash(password)
    user = {
        'email': email,
        'password': hashed_password,
        'name': name,
        'role': role,
        'tone': tone
    }
    result = mongo.db.users.insert_one(user)
    return str(result.inserted_id)

def get_user_by_email(email):
    return mongo.db.users.find_one({'email': email})

def get_user_by_id(user_id):
    return mongo.db.users.find_one({'_id': ObjectId(user_id)})

def verify_password(user, password):
    return check_password_hash(user['password'], password)

def create_or_update_google_user(user_info, token):
    email = user_info['email']
    google_id = user_info['sub']
    name = user_info.get('name', email.split('@')[0])
    avatar = user_info.get('picture')
    
    existing_user = mongo.db.users.find_one({'email': email})
    
    user_data = {
        'google_id': google_id,
        'google_token': token,
        'avatar': avatar,
        'name': name # Update name if from Google
    }
    
    if existing_user:
        mongo.db.users.update_one({'_id': existing_user['_id']}, {'$set': user_data})
        return str(existing_user['_id'])
    else:
        # Create new user
        user_data.update({
            'email': email,
            'role': 'professional', # Default
            'tone': 'formal', # Default
            'created_at': datetime.datetime.utcnow()
        })
        result = mongo.db.users.insert_one(user_data)
        return str(result.inserted_id)

