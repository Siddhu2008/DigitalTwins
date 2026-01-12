from flask import request, jsonify, render_template, url_for
from app.auth import auth_bp
from app.auth.services import create_user, get_user_by_email, verify_password, create_or_update_google_user

from app.auth.utils import generate_token

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('auth/signup.html')
        
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Missing data'}), 400
        
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role', 'professional')
    tone = data.get('tone', 'formal')

    if not email or not password or not name:
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        user_id = create_user(email, password, name, role, tone)
        if not user_id:
            return jsonify({'message': 'User already exists'}), 409

        token = generate_token(user_id)
        return jsonify({'message': 'User created successfully', 'token': token, 'user_id': user_id}), 201
    except Exception as e:
        return jsonify({'message': f"Server Error: {str(e)}"}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')

    data = request.get_json()
    if not data:
        return jsonify({'message': 'Missing data'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing email or password'}), 400

    try:
        user = get_user_by_email(email)
        if not user or not verify_password(user, password):
            return jsonify({'message': 'Invalid credentials'}), 401

        token = generate_token(str(user['_id']))
        return jsonify({'token': token, 'user_name': user['name']}), 200
    except Exception as e:
        return jsonify({'message': f"Server Error: {str(e)}"}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Successfully logged out'}), 200

@auth_bp.route('/google')
def google_login():
    from app.oauth import oauth
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_callback():
    from app.oauth import oauth
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token, None)
    
    user_id = create_or_update_google_user(user_info, token)
    app_token = generate_token(user_id)
    
    # Render a temporary page to save token and redirect
    return render_template('auth/google_callback.html', token=app_token, user_name=user_info.get('name', 'User'))

