from pypew.pypew import create_app
from pypew.models import db

with create_app().app_context():
    db.create_all()
