from pypew import create_app
from models import db

with create_app().app_context():
    db.create_all()
