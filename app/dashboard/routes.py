from flask import render_template, current_app, jsonify, session, redirect, url_for
from app.dashboard import dashboard_bp
from app.auth.utils import token_required
import requests
import datetime

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.loading'))
    return render_template('dashboard/index.html')

@dashboard_bp.route('/calendar')
@token_required
def get_calendar_events(current_user):
    calendar_events = []
    if 'google_token' in current_user and current_user['google_token']:
        try:
            token = current_user['google_token']
            headers = {'Authorization': f"Bearer {token['access_token']}"}
            
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
            params = {
                'timeMin': now,
                'maxResults': 5,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                items = response.json().get('items', [])
                for item in items:
                    calendar_events.append({
                        'summary': item.get('summary', 'No Title'),
                        'start': item['start'].get('dateTime', item['start'].get('date')),
                        'link': item.get('htmlLink')
                    })
        except Exception as e:
            print(f"Error fetching calendar: {e}")
            return jsonify({'error': str(e)}), 500

    return jsonify(calendar_events), 200


