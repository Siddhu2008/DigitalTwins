from flask import render_template, request, jsonify
from app.settings import settings_bp
from app.auth.utils import token_required
from app.db import mongo
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId

@settings_bp.route('/')
def index():
    return render_template('settings/index.html')

@settings_bp.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    # Return safe user data
    user_data = {
        'name': current_user.get('name'),
        'email': current_user.get('email'),
        'role': current_user.get('role', 'professional'),
        'tone': current_user.get('tone', 'formal'),
        'avatar': current_user.get('avatar')
    }
    return jsonify(user_data), 200

@settings_bp.route('/api/profile', methods=['POST'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    updates = {}
    
    if 'name' in data:
        updates['name'] = data['name']
    if 'role' in data:
        updates['role'] = data['role']
    if 'tone' in data:
        updates['tone'] = data['tone']
        
    if updates:
        mongo.db.users.update_one({'_id': current_user['_id']}, {'$set': updates})
        
    return jsonify({'message': 'Profile updated successfully'}), 200

@settings_bp.route('/api/password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password or len(new_password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters'}), 400
        
    hashed_password = generate_password_hash(new_password)
    mongo.db.users.update_one({'_id': current_user['_id']}, {'$set': {'password': hashed_password}})
    
    return jsonify({'message': 'Password changed successfully'}), 200
