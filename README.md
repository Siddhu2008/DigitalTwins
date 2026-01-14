# Digital Twins - Meeting Analytics Platform

A comprehensive web application for analyzing and managing virtual meetings with real-time collaboration features, tone analysis, and meeting insights.

## Project Overview

**Digital Twins** is a Flask-based meeting analytics platform that integrates Google Calendar, enables real-time video collaboration, performs voice tone analysis, and provides detailed meeting insights and analytics. The application uses WebSocket technology for real-time communication and MongoDB for data persistence.

### Key Features

- 🔐 **Google OAuth Authentication** - Secure login via Google accounts
- 📅 **Calendar Integration** - Sync and manage meetings with Google Calendar
- 🎥 **Real-time Video Meetings** - WebSocket-based meeting room functionality
- 🎙️ **Tone Analysis** - Analyze speaker tone and sentiment during meetings
- 📊 **Meeting Analytics** - Track and visualize meeting metrics and insights
- 💬 **Dashboard** - Central hub for viewing call history and meeting overview
- ⚙️ **User Settings** - Manage user preferences and configurations

## Tech Stack

### Backend
- **Framework**: Flask
- **Database**: MongoDB
- **Authentication**: Google OAuth 2.0 (Authlib)
- **Real-time Communication**: Flask-SocketIO, WebSocket
- **API**: RESTful with CORS support

### Frontend
- **Templates**: Jinja2 HTML
- **Charting**: Chart.js
- **Styling**: CSS

### Key Dependencies
- `Flask` - Web framework
- `Flask-PyMongo` - MongoDB integration
- `PyJWT` - JWT token handling
- `Authlib` - OAuth implementation
- `Flask-SocketIO` - WebSocket support
- `python-dotenv` - Environment configuration

## Project Structure

```
FINALDigitaltwins/
├── app/
│   ├── auth/               # Authentication routes and services
│   ├── dashboard/          # Dashboard views
│   ├── meet/               # Meeting room functionality
│   ├── meetings/           # Meeting management
│   ├── tone/               # Tone analysis features
│   ├── settings/           # User settings
│   ├── static/             # CSS, JavaScript, images
│   ├── templates/          # HTML templates
│   ├── __init__.py         # App factory
│   ├── db.py               # Database setup
│   ├── oauth.py            # OAuth configuration
│   └── socket.py           # WebSocket setup
├── config.py               # Configuration settings
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies
└── .env.example            # Environment variables template
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB running locally or remote instance
- Google OAuth credentials (Client ID and Secret)
- Node.js (optional, for frontend assets)

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd FINALDigitaltwins

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (optional)
npm install
```

### Step 2: Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
```

**Required environment variables**:
```
SECRET_KEY=your_secret_key_here
MONGO_URI=mongodb://localhost:27017/auralis_db
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Step 3: Run the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## API Routes

### Authentication (`/auth`)
- `GET /auth/login` - Initiate Google OAuth login
- `GET /auth/callback` - Google OAuth callback
- `POST /auth/logout` - Logout user

### Dashboard (`/dashboard`)
- `GET /dashboard/` - Main dashboard page

### Meetings (`/meetings`)
- `GET /meetings/` - List all meetings
- `POST /meetings/` - Create a new meeting
- `GET /meetings/<id>` - Get meeting details

### Tone Analysis (`/tone`)
- `GET /tone/` - Tone analysis page
- `POST /tone/analyze` - Analyze tone data

### Meet Room (`/meet`)
- `GET /meet/room` - Enter video meeting room

### Settings (`/settings`)
- `GET /settings/` - User settings page

## Real-time Features

The application uses **Flask-SocketIO** for real-time bidirectional communication:

- Live meeting updates
- Real-time tone analysis feedback
- Instant notification delivery
- WebSocket connection management

## Database Schema (MongoDB)

Collections:
- `users` - User profiles and authentication data
- `meetings` - Meeting records and metadata
- `analytics` - Meeting analytics and metrics
- `tone_analysis` - Tone and sentiment analysis results

## Configuration

Edit `config.py` to customize:
- Secret key for sessions
- MongoDB connection URI
- Upload folder for media
- Maximum file size (16MB default)
- CORS allowed origins

## Development

### Debug Mode
The application runs in debug mode by default in `run.py`. This enables:
- Auto-reloading on code changes
- Detailed error messages
- Interactive debugger

### Adding New Routes

1. Create a new module in `app/`
2. Define routes and views
3. Register blueprint in `app/__init__.py`

Example:
```python
from flask import Blueprint
my_bp = Blueprint('my_feature', __name__)

@my_bp.route('/')
def index():
    return 'Hello'

app.register_blueprint(my_bp, url_prefix='/my_feature')
```

## Deployment

For production:
1. Set `DEBUG=False` in Flask
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Set strong `SECRET_KEY`
4. Configure proper MongoDB instance
5. Set up HTTPS/SSL certificates
6. Use environment-specific `.env` files

Example with Gunicorn:
```bash
gunicorn --worker-class eventlet -w 1 run:app
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

Specify your project license here.

## Support

For issues or questions, please open an issue on GitHub or contact the development team.

---

**Last Updated**: January 2026
