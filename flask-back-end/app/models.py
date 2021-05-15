from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Galaxy(db.Model):
    __tablename__ = 'galaxy'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))   
    right_ascension = db.Column(db.Float(32))
    declination = db.Column(db.Float(32))
    coordinate_system = db.Column(db.String(128))
    redshift = db.Column(db.Float(32))
    lensing_flag = db.Column(db.String(32))
    classification = db.Column(db.String(128))   
    notes = db.Column(db.String(128))
    lines = db.relationship('Line', backref='galaxy', lazy='dynamic')  

class Line(db.Model):
    __tablename__ = 'line'
    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxy.id') ) 
    j_upper = db.Column(db.Integer)  
    line_id_type = db.Column(db.String(32))
    integrated_line_flux = db.Column(db.Float(32), nullable = False)
    integrated_line_flux_uncertainty_positive = db.Column(db.Float(32))
    integrated_line_flux_uncertainty_negative = db.Column(db.Float(32))
    peak_line_flux = db.Column(db.Float(32))
    peak_line_flux_uncertainty_positive = db.Column(db.Float(32))
    peak_line_flux_uncertainty_negative = db.Column(db.Float(32))
    line_width = db.Column(db.Float(32))
    line_width_uncertainty_positive = db.Column(db.Float(32))
    line_width_uncertainty_negative = db.Column(db.Float(32))
    observed_line_frequency = db.Column(db.Float(32))
    observed_line_frequency_uncertainty_positive = db.Column(db.Float(32))
    observed_line_frequency_uncertainty_negative = db.Column(db.Float(32))
    detection_type = db.Column(db.String(32))
    observed_beam_major = db.Column(db.Float(32))
    observed_beam_minor = db.Column(db.Float(32))
    observed_beam_angle = db.Column(db.Float(32))
    reference = db.Column(db.String(128))
    notes = db.Column(db.String(128))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    #generates a password hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    #checks if the password hash corresponds to a password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    #returns printable representaion of the object
    def __repr__(self):
        return '<User {}>'.format(self.username)

#function that will provide a user to the flask-login, given the user's ID
@login.user_loader
def load_user(id):
    return User.query.get(int(id))