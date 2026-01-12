from flask import Blueprint

tone_bp = Blueprint('tone', __name__)

from app.tone import routes
