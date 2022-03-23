from sqlalchemy.orm import backref
from ._db import db
from datetime import datetime

class BaseMixin(object):

    @classmethod
    def delete(cls, **kwargs):
        obj = cls(**kwargs)
        db.session.delete(obj)
        db.session.commit()

    @classmethod
    def delete_object(cls, obj):
        db.session.delete(obj)
        db.session.commit()

    @classmethod
    def approve(cls, **kwargs):
        obj = cls(**kwargs)
        db.session.add(obj)
        db.session.commit()
    
    @classmethod
    def approve_object(cls, obj):
        db.session.add(obj)
        db.session.commit()


class Post(db.Model):
    __tablename__ = 'post'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))
    time_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    tempgalaxy_id = db.Column(db.Integer, db.ForeignKey('tempgalaxy.id'))
    templine_id = db.Column(db.Integer, db.ForeignKey('templine.id'))  
    editgalaxy_id = db.Column(db.Integer, db.ForeignKey('editgalaxy.id'))
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxy.id'))
    editline_id = db.Column(db.Integer, db.ForeignKey('editline.id'))  
    tempgalaxies = db.relationship('TempGalaxy', backref='post', foreign_keys=[tempgalaxy_id])
    templines = db.relationship('TempLine', backref='post', foreign_keys=[templine_id])
    editgalaxies = db.relationship('EditGalaxy', backref='post', foreign_keys=[editgalaxy_id])
    galaxies = db.relationship('Galaxy', backref='post', foreign_keys=[galaxy_id])
    editlines = db.relationship('EditLine', backref='post', foreign_keys=[editline_id])

class Galaxy(BaseMixin, db.Model):
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
    time_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    lines = db.relationship('Line', backref='galaxy', lazy='dynamic')  
    approved_user_email = db.Column(db.String(128))
    approved_username = db.Column(db.String(128))
    approved_time = db.Column(db.DateTime, default=datetime.utcnow)



    def as_dict(self):
        return {'name': self.name}

class TempGalaxy(BaseMixin, db.Model):
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
    admin_notes = db.Column(db.String(128))
    time_submitted = db.Column(db.DateTime, default=datetime.utcnow)


    def as_dict(self):
        return {'name': self.name}

    def get_ra(self):
        return self.right_ascension

    def get_dec(self):
        return self.declination

    def __repr__(self):
        return '{}'.format(self.id)
    
class EditGalaxy(db.Model):
    __tablename__ = 'editgalaxy'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable = False)
    is_similar = db.Column(db.String(128))
    is_edited = db.Column(db.String(128))    
    right_ascension = db.Column(db.Float(32)) 
    declination = db.Column(db.Float(32)) 
    coordinate_system = db.Column(db.String(128), nullable = False)
    redshift = db.Column(db.Float(32))
    redshift_error = db.Column(db.Float(32))
    lensing_flag = db.Column(db.String(32), nullable = False)
    classification = db.Column(db.String(128), nullable = False)   
    notes = db.Column(db.String(128))
    user_submitted = db.Column(db.String(128))
    user_email = db.Column(db.String(128))
    admin_notes = db.Column(db.String(128))
    time_submitted = db.Column(db.DateTime, default=datetime.utcnow)
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
    emitted_frequency = db.Column(db.Float(32), nullable = False)
    species = db.Column(db.String(32))
    integrated_line_flux = db.Column(db.Float(32))
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
    time_submitted = db.Column(db.DateTime)
    approved_user_email = db.Column(db.String(128))
    approved_username = db.Column(db.String(128))
    approved_time = db.Column(db.DateTime, default=datetime.utcnow)
    right_ascension = db.Column(db.Float(32)) 
    declination = db.Column(db.Float(32)) 



class TempLine(db.Model):
    __tablename__ = 'templine'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer) 
    from_existed_id = db.Column(db.Integer)
    emitted_frequency = db.Column(db.Float(32), nullable = False)
    species = db.Column(db.String(32))
    integrated_line_flux = db.Column(db.Float(32))
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
    time_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    galaxy_name = db.Column(db.String(128))
    right_ascension = db.Column(db.Float(32)) 
    declination = db.Column(db.Float(32)) 


class EditLine(db.Model):
    __tablename__ = 'editline'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxy.id')) 
    original_line_id = db.Column(db.Integer)
    is_edited = db.Column(db.String(128))  
    emitted_frequency = db.Column(db.Float(32), nullable = False)
    species = db.Column(db.String(32))
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
    time_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    galaxy_name = db.Column(db.String(128))
    right_ascension = db.Column(db.Float(32)) 
    declination = db.Column(db.Float(32)) 







