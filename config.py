import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_change_in_production'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://sawhuman2008_db_user:SIDDHUk2008@cluster0.uis5qkl.mongodb.net/auralis_db?appName=Cluster0'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16MB max limit

    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')


