from enum import unique
from flask_login.login_manager import LoginManager
from ._db import db
from ._bcrypt import bcrypt
#from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from datetime import datetime
from ._login import my_login_manager



class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120, collation='NOCASE'), index=True, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    university = db.Column(db.String(120))
    website = db.Column(db.String(120))
    password_hash = db.Column(db.String(128), nullable=False)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')

    #returns printable representaion of the object
    def __repr__(self):
        return '<User {}>'.format(self.username)

    #generates a password hash
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('UTF-8')
    
    #checks if the password hash corresponds to a password
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    #method of class User, which takes the email of the user, and asks gravatar services to provide the image associated with the email or randomly generated image instead.
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def get_user_by_token(token):
        return User.query.get(int(token))

    def has_roles(self, *args):
        return set(args).issubset({role.name for role in self.roles})

#function that will provide a user to the flask-login, given the user's ID
@my_login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

