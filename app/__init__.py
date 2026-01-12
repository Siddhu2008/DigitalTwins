from flask import Flask
from config import Config
from app.db import mongo

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    mongo.init_app(app)

    from app.oauth import oauth
    oauth.init_app(app)
    
    from app.socket import socketio
    socketio.init_app(app, cors_allowed_origins="*")

    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile https://www.googleapis.com/auth/calendar.readonly'
        }
    )


    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    from app.meetings import meetings_bp
    app.register_blueprint(meetings_bp, url_prefix='/meetings')

    from app.tone import tone_bp
    app.register_blueprint(tone_bp, url_prefix='/tone')

    from app.settings import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from app.meet import meet_bp
    app.register_blueprint(meet_bp, url_prefix='/meet')

    @app.route('/')
    def index():
        from flask import redirect
        return redirect('/dashboard/')

    return app

