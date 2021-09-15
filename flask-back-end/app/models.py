from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from datetime import datetime

class Galaxy(db.Model):
    __tablename__ = 'galaxy'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable = False) 
    is_similar = db.Column(db.String(128))
    is_edited = db.Column(db.String(128))  
    right_ascension = db.Column(db.Float(32), nullable = False) 
    declination = db.Column(db.Float(32), nullable = False) 
    coordinate_system = db.Column(db.String(128), nullable = False)
    redshift = db.Column(db.Float(32))
    redshift_error = db.Column(db.Float(32))
    lensing_flag = db.Column(db.String(32), nullable = False)
    classification = db.Column(db.String(128), nullable = False)   
    notes = db.Column(db.String(128))
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))
    lines = db.relationship('Line', backref='galaxy', lazy='dynamic')  

    def as_dict(self):
        return {'name': self.name}

class TempGalaxy(db.Model):
    __tablename__ = 'tempgalaxy'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable = False)
    is_similar = db.Column(db.String(128))
    right_ascension = db.Column(db.Float(32), nullable = False) 
    declination = db.Column(db.Float(32), nullable = False) 
    coordinate_system = db.Column(db.String(128), nullable = False)
    redshift = db.Column(db.Float(32))
    redshift_error = db.Column(db.Float(32))
    lensing_flag = db.Column(db.String(32), nullable = False)
    classification = db.Column(db.String(128), nullable = False)   
    notes = db.Column(db.String(128))
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))
    lines = db.relationship('TempLine', backref='tempgalaxy', lazy='dynamic')  
    admin_notes = db.Column(db.String(128))

    def as_dict(self):
        return {'name': self.name}

    def get_ra(self):
        return self.right_ascension

    def get_dec(self):
        return self.declination

    def __repr__(self):
        return '{}'.format(self.name)
    
class EditGalaxy(db.Model):
    __tablename__ = 'editgalaxy'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable = False)
    is_similar = db.Column(db.String(128))
    is_edited = db.Column(db.String(128))    
    right_ascension = db.Column(db.Float(32), nullable = False) 
    declination = db.Column(db.Float(32), nullable = False) 
    coordinate_system = db.Column(db.String(128), nullable = False)
    redshift = db.Column(db.Float(32))
    redshift_error = db.Column(db.Float(32))
    lensing_flag = db.Column(db.String(32), nullable = False)
    classification = db.Column(db.String(128), nullable = False)   
    notes = db.Column(db.String(128))
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))
    lines = db.relationship('EditLine', backref='editgalaxy', lazy='dynamic')  
    admin_notes = db.Column(db.String(128))
    original_id = db.Column(db.Integer)

    def as_dict(self):
        return {'name': self.name}

    def get_ra(self):
        return self.right_ascension

    def get_dec(self):
        return self.declination

    def __repr__(self):
        return '{}'.format(self.name)
    

class Line(db.Model):
    __tablename__ = 'line'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxy.id')) 
    j_upper = db.Column(db.Integer, nullable = False)  
    integrated_line_flux = db.Column(db.Float(32), nullable = False)
    integrated_line_flux_uncertainty_positive = db.Column(db.Float(32), nullable = False)
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
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))

class TempLine(db.Model):
    __tablename__ = 'templine'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('tempgalaxy.id')) 
    from_existed_id = db.Column(db.Integer)
    j_upper = db.Column(db.Integer, nullable = False)  
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
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))
    admin_notes = db.Column(db.String(128))

class EditLine(db.Model):
    __tablename__ = 'editline'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('editgalaxy.id')) 
    from_existed_id = db.Column(db.Integer)
    j_upper = db.Column(db.Integer, nullable = False)  
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
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))
    admin_notes = db.Column(db.String(128))


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    university = db.Column(db.String(120))
    website = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    #returns printable representaion of the object
    def __repr__(self):
        return '<User {}>'.format(self.username)

    #generates a password hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    #checks if the password hash corresponds to a password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    #method of class User, which takes the email of the user, and asks gravatar services to provide the image associated with the email or randomly generated image instead.
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

#function that will provide a user to the flask-login, given the user's ID
@login.user_loader
def load_user(id):
    return User.query.get(int(id))