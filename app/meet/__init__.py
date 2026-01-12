from flask import Blueprint

meet_bp = Blueprint('meet', __name__)

from app.meet import routes, events
