import os
import google.generativeai as genai
from app.db import mongo
from datetime import datetime
from bson.objectid import ObjectId

class PersonaService:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    def analyze_user_speaking_style(self, user_id):
        """Analyzes transcripts from user's past meetings to build a persona."""
        # 1. Fetch recent transcripts for this user
        # We need to find transcripts where 'speaker' matches user's name
        # First get user's name
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return None
            
        name = user.get('name', '')
        
        # Get last 1000 transcript entries for this user
        cursor = mongo.db.transcripts.find({'speaker': name}).sort('timestamp', -1).limit(1000)
        transcripts = list(cursor)
        
        if len(transcripts) < 10:
            return {
                'status': 'insufficient_data',
                'message': 'Need more meeting data to generate persona (min 10 lines)'
            }
            
        text_samples = "\n".join([t['text'] for t in transcripts])
        
        # 2. Analyze with Gemini
        prompt = f"""
        Analyze the following speech samples from a user named {name} to create a digital twin persona.
        Identify their speaking style, tone, common vocabulary, sentence length, and personality traits.
        
        Speech Samples:
        {text_samples[:10000]}  # Limit characters to avoid token limits
        
        Return a JSON object with:
        - speaking_style (string): e.g. "Professional and concise", "Casual and friendly"
        - tone (string): e.g. "Authoritative", "Collaborative"
        - vocabulary_level (string): "Simple", "Technical", "Academic"
        - key_phrases (list): Common phrases they use
        - system_prompt (string): A instruction paragraph I can give to an AI to make it act like this user.
          Start with "You are acting as [Name]..."
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Simple cleanup if it returns markdown json
            text = response.text.replace('```json', '').replace('```', '')
            import json
            analysis = json.loads(text)
            
            # 3. Save to Personas collection
            persona_doc = {
                'user_id': user_id,
                'name': name,
                'analysis': analysis,
                'generated_prompt': analysis.get('system_prompt', ''),
                'updated_at': datetime.utcnow()
            }
            
            mongo.db.personas.update_one(
                {'user_id': user_id},
                {'$set': persona_doc},
                upsert=True
            )
            
            return persona_doc
            
        except Exception as e:
            print(f"Error generating persona: {e}")
            return None

    def get_persona(self, user_id):
        return mongo.db.personas.find_one({'user_id': user_id})

    def get_system_prompt(self, user_id):
        persona = self.get_persona(user_id)
        if persona:
            return persona.get('generated_prompt')
        return None
