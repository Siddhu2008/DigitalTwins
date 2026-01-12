from flask import Blueprint

meetings_bp = Blueprint('meetings', __name__)

from app.meetings import routes
