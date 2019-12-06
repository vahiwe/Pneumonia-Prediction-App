from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from flask_login import UserMixin
from app import login
from hashlib import md5


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    photo = db.Column(db.String(64))
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    gender = db.Column(db.String(64))
    profession = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    email_confirmation_sent_on = db.Column(
        db.DateTime, default=datetime.utcnow)
    email_confirmed = db.Column(db.Boolean, nullable=True, default=False)
    email_confirmed_on = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient = db.Column(db.String(120))
    photo = db.Column(db.String(64))
    photo_url = db.Column(db.String(120))
    status = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_email = db.Column(db.String(64), db.ForeignKey('user.email'))
