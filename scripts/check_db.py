from app import create_app
from app.db import mongo
from bson import ObjectId

app = create_app()

with app.app_context():
    print("=== Active Meetings ===")
    for m in mongo.db.active_meetings.find():
        print(m)
        
    print("\n=== Transcripts ===")
    for t in mongo.db.transcripts.find().limit(10):
        print(t)
        
    print("\n=== Meetings (Metadata) ===")
    for m in mongo.db.meetings.find().limit(5):
        print(m)
