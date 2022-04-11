from enum import unique
from ._db import db
from hashlib import md5
from datetime import datetime
from flask_security import UserMixin, RoleMixin


roles_users = db.Table('roles_users',
                        db.Column('user_id',
                        db.ForeignKey('user.id')),
                        db.Column('role_id',
                        db.ForeignKey('role.id')),

)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    confirmed_at = db.Column(db.DateTime())
    university = db.Column(db.String(120))
    website = db.Column(db.String(120))
    #password_hash = db.Column(db.String(128), nullable=False)
    about_me = db.Column(db.String(140))
    #last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users'), lazy='dynamic')

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)


