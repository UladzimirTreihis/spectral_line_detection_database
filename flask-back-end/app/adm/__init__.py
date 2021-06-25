from flask import Blueprint, url_for, redirect, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.actions import action
from app.models import User, Galaxy, Line, TempGalaxy, TempLine
from app import admin, db, Session


bp = Blueprint('adm', __name__)

class TempGalaxyView(ModelView):
    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            galaxy = session.query(TempGalaxy.name, TempGalaxy.right_ascension, TempGalaxy.declination, TempGalaxy.coordinate_system, TempGalaxy.lensing_flag, TempGalaxy.classification, TempGalaxy.notes).filter(TempGalaxy.id==id).all()
            g = Galaxy (name = galaxy[0][0], right_ascension = galaxy[0][1], declination = galaxy[0][2], coordinate_system = galaxy[0][3], lensing_flag = galaxy [0][4], classification = galaxy[0][5], notes = galaxy [0][6])
            db.session.add (g)
            db.session.commit ()
            g_temp = TempGalaxy.query.filter_by(id=id).first()
            db.session.delete (g_temp)
            db.session.commit ()
            flash ("Galaxy has been Added")            
        
class TempLineView(ModelView):
    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            line = session.query(TempLine.galaxy_id, TempLine.j_upper, TempLine.integrated_line_flux, TempLine.integrated_line_flux_uncertainty_positive, TempLine.integrated_line_flux_uncertainty_negative, TempLine.peak_line_flux, TempLine.peak_line_flux_uncertainty_positive, TempLine.peak_line_flux_uncertainty_negative, TempLine.line_width, TempLine.line_width_uncertainty_positive, TempLine.line_width_uncertainty_negative, TempLine.observed_line_frequency, TempLine.observed_line_frequency_uncertainty_positive, TempLine.observed_line_frequency_uncertainty_negative, TempLine.detection_type, TempLine.observed_beam_major, TempLine.observed_beam_minor, TempLine.observed_beam_angle, TempLine.reference, TempLine.notes).filter(TempLine.id==id).all()
            l = Line (galaxy_id = line [0][0], j_upper = line [0][1], integrated_line_flux = line [0][2], integrated_line_flux_uncertainty_positive = line [0][3], integrated_line_flux_uncertainty_negative = line [0][4], peak_line_flux = line [0][5], peak_line_flux_uncertainty_positive = line [0][6], peak_line_flux_uncertainty_negative = line [0][7], line_width = line [0][8], line_width_uncertainty_positive = line [0][9], line_width_uncertainty_negative = line [0][10], observed_line_frequency = line [0][11], observed_line_frequency_uncertainty_positive = line [0][12], observed_line_frequency_uncertainty_negative = line [0][13], detection_type = line [0][14], observed_beam_major = line [0][15], observed_beam_minor = line [0][16], observed_beam_angle = line [0][17], reference = line [0][18], notes = line [0][19])
            db.session.add (l)
            db.session.commit ()
            l_temp = TempLine.query.filter_by(id=id).first()
            db.session.delete (l_temp)
            db.session.commit ()

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Galaxy, db.session))
admin.add_view(ModelView(Line, db.session))
admin.add_view(TempGalaxyView (TempGalaxy, db.session, category = "New Entries"))
admin.add_view(TempLineView(TempLine, db.session, category = "New Entries"))

