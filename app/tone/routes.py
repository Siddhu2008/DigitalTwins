from flask import render_template, request, jsonify
from app.tone import tone_bp
from app.tone.services import get_tone_profile, analyze_text_sample
from app.auth.utils import token_required

@tone_bp.route('/', methods=['GET'])
def index():
    return render_template('tone/index.html')

@tone_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    profile = get_tone_profile(str(current_user['_id']))
    if '_id' in profile:
        profile['_id'] = str(profile['_id'])
    return jsonify(profile), 200

@tone_bp.route('/analyze', methods=['POST'])
@token_required
def analyze(current_user):
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'message': 'No text provided'}), 400
        
    profile = analyze_text_sample(str(current_user['_id']), data['text'])
    if '_id' in profile:
        profile['_id'] = str(profile['_id'])
        
    return jsonify({'message': 'Tone analyzed successfully', 'profile': profile}), 200
