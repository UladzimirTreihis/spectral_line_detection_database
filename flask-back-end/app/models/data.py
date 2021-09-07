from ._db import db
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


