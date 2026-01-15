import os
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.meetings import meetings_bp
from app.meetings.services import save_meeting_metadata, process_meeting, get_meeting_by_id, get_summary_by_meeting_id, get_user_meetings
from app.auth.utils import token_required

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'wav', 'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@meetings_bp.route('/upload', methods=['POST'])
@token_required
def upload(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Save metadata
        meeting_id = save_meeting_metadata(str(current_user['_id']), filename, filename)
        
        # Trigger processing (Real)
        process_meeting(meeting_id)
        
        return jsonify({'message': 'File uploaded and processed', 'meeting_id': meeting_id}), 201
    
    return jsonify({'message': 'File type not allowed'}), 400

@meetings_bp.route('/', methods=['GET'])
@token_required
def list_meetings(current_user):
    meetings = get_user_meetings(str(current_user['_id']))
    # Convert ObjectIds to strings for JSON serialization
    for m in meetings:
        m['_id'] = str(m['_id'])
        m['created_at'] = m['created_at'].isoformat()
        if 'ended_at' in m and m['ended_at']:
            m['ended_at'] = m['ended_at'].isoformat()
    return jsonify(meetings), 200

@meetings_bp.route('/<meeting_id>/summary', methods=['GET'])
@token_required
def get_summary(current_user, meeting_id):
    summary = get_summary_by_meeting_id(meeting_id)
    if not summary:
        return jsonify({'message': 'Summary not found'}), 404
        
    summary['_id'] = str(summary['_id'])
    return jsonify(summary), 200
