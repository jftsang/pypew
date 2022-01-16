from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    precedence = db.Column(db.Boolean)