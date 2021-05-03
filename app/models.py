from app import db

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