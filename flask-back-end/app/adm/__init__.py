from flask import Blueprint, url_for, redirect, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose, BaseView
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.actions import action
from flask_admin.contrib.sqla import form, filters as sqla_filters, tools
from flask_user import login_required, roles_required
from app.models import User, Galaxy, Line, TempGalaxy, TempLine, Role
from app import admin, db, Session
from config import EMITTED_FREQUENCY
from sqlalchemy import func
from app.main.routes import galaxy, within_distance, ra_to_float, dec_to_float

bp = Blueprint('adm', __name__)

def update_redshift(session, galaxy_id):
    line_redshift = session.query(
            Line.j_upper, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
        ).outerjoin(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).all() 

    sum_upper = sum_lower = 0
    for l in line_redshift:
        #This if ignores all line without nu or nu_uncertainty in calculating galaxy's redshift. 
        if l.observed_line_frequency or l.observed_line_frequency_uncertainty_positive == None:
            continue
        if l.observed_line_frequency_uncertainty_negative == None:
            delta_nu = 2 * l.observed_line_frequency_uncertainty_positive
        else:
            delta_nu = l.observed_line_frequency_uncertainty_positive + l.observed_line_frequency_uncertainty_negative
        J_UPPER = l.j_upper
        if J_UPPER > 30 or J_UPPER < 1:
            continue
        z = (EMITTED_FREQUENCY.get(J_UPPER) - l.observed_line_frequency) / l.observed_line_frequency
        delta_z = ((1 + z) * delta_nu) / l.observed_line_frequency
        sum_upper = sum_upper =+ (z/delta_z)
        sum_lower = sum_lower =+ (1/delta_z)
    if sum_lower == 0:
        sum_upper = -1
        return sum_upper
    redshift_weighted = sum_upper / sum_lower
    session.query(Galaxy).filter(
        Galaxy.id == galaxy_id
    ).update({"redshift": redshift_weighted})
    session.commit()
    
    return sum_upper

def update_redshift_error(session, galaxy_id, sum_upper):
    #the while statement checks if the redshift was updated
    while sum_upper != -1:
        redshift_error_weighted = 0
        line_redshift = session.query(
                Line.j_upper, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
            ).outerjoin(Galaxy).filter(
                Galaxy.id == galaxy_id
            ).all() 
        for l in line_redshift:
            #This if ignores all line without nu or nu_uncertainty in calculating galaxy's redshift. 
            if l.observed_line_frequency or l.observed_line_frequency_uncertainty_positive == None:
                continue
            if l.observed_line_frequency_uncertainty_negative == None:
                delta_nu = 2 * l.observed_line_frequency_uncertainty_positive
            else:
                delta_nu = l.observed_line_frequency_uncertainty_positive + l.observed_line_frequency_uncertainty_negative
            J_UPPER = l.j_upper
            z = (EMITTED_FREQUENCY.get(J_UPPER) - l.observed_line_frequency) / l.observed_line_frequency
            delta_z = ((1 + z) * delta_nu) / l.observed_line_frequency
            weight = (z/delta_z)/sum_upper
            redshift_error_weighted = redshift_error_weighted =+ (weight*delta_z)
        session.query(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).update({"redshift_error": redshift_error_weighted})
        session.commit()
        sum_upper = -1


class TempGalaxyView(ModelView):

    #edit_template = 'admin/model/temp_galaxy_edit.html'
    #list_template = 'admin/model/temp_galaxy_list.html'
    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            galaxy = session.query(TempGalaxy.name, TempGalaxy.right_ascension, TempGalaxy.declination, TempGalaxy.coordinate_system, TempGalaxy.lensing_flag, TempGalaxy.classification, TempGalaxy.notes).filter(TempGalaxy.id==id).all()
            g = Galaxy (name = galaxy[0][0], right_ascension = galaxy[0][1], declination = galaxy[0][2], coordinate_system = galaxy[0][3], lensing_flag = galaxy [0][4], classification = galaxy[0][5], notes = galaxy [0][6])
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            existed = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == id).update({TempLine.from_existed_id: existed})
            g_temp = TempGalaxy.query.filter_by(id=id).first()
            db.session.delete (g_temp)
            db.session.commit ()
            flash ("Galaxy has been Added")            
        
    @action('check for similar', 'Check For Similar')
    def action_check_for_similar(self, ids):
        session=Session()
        for id in ids:
            galaxy = session.query(TempGalaxy).filter(TempGalaxy.id == id)
            RA_list = [g.get_ra() for g in galaxy]
            RA = RA_list[0]
            DEC_list = [g.get_dec() for g in galaxy]
            DEC = DEC_list[0]
            #RA = session.query(TempGalaxy.get_ra).filter(TempGalaxy.id==id).first()
            #DEC = session.query(TempGalaxy.get_dec).filter(TempGalaxy.id==id).first()
            #RA = session.query(TempGalaxy.right_ascension).filter(TempGalaxy.id==id).first()
            #DEC = session.query(TempGalaxy.declination).filter(TempGalaxy.id==id).first()
            galaxies=session.query(Galaxy, Line).outerjoin(Line)
            galaxies = within_distance(session, galaxies, RA, DEC, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name).first()
            if galaxies == None:
                continue
            similar_galaxy_id = str(galaxies)
            similar_galaxy_id = int(similar_galaxy_id[9:similar_galaxy_id.find('>')])
            similar_galaxy = session.query(Galaxy.name).filter(Galaxy.id == similar_galaxy_id).first()
            similar_galaxy_name = str(similar_galaxy)
            similar_galaxy_name = similar_galaxy_name [2:similar_galaxy_name.find(',')-1]

            session.query(TempGalaxy).filter(TempGalaxy.id==id).update({"admin_notes": similar_galaxy_name})
            session.commit()


class TempLineView(ModelView):
    #details_template = "/admin/model/templine.html"
    #list_template = "/admin/model/templine.html"
    #@expose('/templine/')
    #def templine(self):
        #return self.render('/admin/model/templine.html')

    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            line = session.query(TempLine.galaxy_id, TempLine.j_upper, TempLine.integrated_line_flux, TempLine.integrated_line_flux_uncertainty_positive, TempLine.integrated_line_flux_uncertainty_negative, TempLine.peak_line_flux, TempLine.peak_line_flux_uncertainty_positive, TempLine.peak_line_flux_uncertainty_negative, TempLine.line_width, TempLine.line_width_uncertainty_positive, TempLine.line_width_uncertainty_negative, TempLine.observed_line_frequency, TempLine.observed_line_frequency_uncertainty_positive, TempLine.observed_line_frequency_uncertainty_negative, TempLine.detection_type, TempLine.observed_beam_major, TempLine.observed_beam_minor, TempLine.observed_beam_angle, TempLine.reference, TempLine.notes, TempLine.from_existed_id).filter(TempLine.id==id).all()
            
            if (line [0][20] == None):
                raise Exception('You have not yet approved the galaxy to whoch the line belongs to')
            else:
                g_id = line [0][20]
            l = Line (galaxy_id = g_id, j_upper = line [0][1], integrated_line_flux = line [0][2], integrated_line_flux_uncertainty_positive = line [0][3], integrated_line_flux_uncertainty_negative = line [0][4], peak_line_flux = line [0][5], peak_line_flux_uncertainty_positive = line [0][6], peak_line_flux_uncertainty_negative = line [0][7], line_width = line [0][8], line_width_uncertainty_positive = line [0][9], line_width_uncertainty_negative = line [0][10], observed_line_frequency = line [0][11], observed_line_frequency_uncertainty_positive = line [0][12], observed_line_frequency_uncertainty_negative = line [0][13], detection_type = line [0][14], observed_beam_major = line [0][15], observed_beam_minor = line [0][16], observed_beam_angle = line [0][17], reference = line [0][18], notes = line [0][19])
            db.session.add (l)
            total = update_redshift(session, g_id)
            update_redshift_error(session, g_id, total)
            db.session.commit ()
            l_temp = TempLine.query.filter_by(id=id).first()
            db.session.delete (l_temp)
            db.session.commit ()

    @action('delete',
           'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):
        session = Session ()
        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        if self.fast_mass_delete:
            count = query.delete(synchronize_session=False)
        else:
            count = 0
            for m in query.all():
                if self.delete_model(m):
                    count += 1
        self.session.commit()
        for id in ids:
            g_id = session.query(TempLine.galaxy_id).filter(TempLine.id==id).first()
            total = update_redshift(session, g_id)
            update_redshift_error(session, g_id, total)
            db.session.commit ()
        flash('Record was successfully deleted.')

class PostsView(BaseView):
    @expose('/')
    def post_view(self):
        line = "hi"
        #self.line = line
        return self.render("/admin/posts.html", line=line)




admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Role, db.session))
admin.add_view(ModelView(Galaxy, db.session))
#admin.add_view(ModelView(Line, db.session))
admin.add_view(PostsView(name='Posts', endpoint='posts'))
admin.add_view(TempGalaxyView (TempGalaxy, db.session, category = "New Entries"))
admin.add_view(TempLineView(TempLine, db.session, category = "New Entries"))

