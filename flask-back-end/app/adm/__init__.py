from flask import Blueprint, url_for, redirect, flash, request
from flask.cli import with_appcontext
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, expose, BaseView, AdminIndexView
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.actions import action
from flask_admin.contrib.sqla import form, filters as sqla_filters, tools
from app.models import User, Galaxy, Line, TempGalaxy, TempLine, Role, Post, EditGalaxy, EditLine
from app import db, Session, admin, user_datastore
from config import EMITTED_FREQUENCY
from sqlalchemy import func
from flask_security import current_user
from app.main.routes import galaxy, within_distance, ra_to_float, dec_to_float
from wtforms.validators import Regexp, ValidationError
from config import dec_reg_exp, ra_reg_exp


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

class GalaxyView (ModelView):
    def check_coords(form, coordinate_system):
        if form.coordinate_system.data != "ICRS" and form.coordinate_system.data != "J2000":
            raise ValidationError('Coordinate System must be either J2000 or ICRS')

    def check_lensing_flag (form, lensing_flag):
        if form.lensing_flag.data != "Lensed" and form.lensing_flag.data != "Unlensed" and form.lensing_flag.data != "Either":
            raise ValidationError('Lensing Flag can only be Lensed, Unlensed or Either')

    form_args = dict(
        coordinate_system=dict(validators=[check_coords]),
        lensing_flag = dict(validators=[check_lensing_flag]),
        right_ascension = dict(validators = [Regexp(ra_reg_exp, message="Input in the format 00h00m00s or as a float")]),
        declination = dict(validators = [Regexp(dec_reg_exp, message="Input in the format (+/-) 00h00m00s or as a float")]),
    )


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

class EditGalaxyView(ModelView):
    
    #edit_template = 'admin/model/temp_galaxy_edit.html'
    #list_template = 'admin/model/temp_galaxy_list.html'
    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            galaxy = session.query(EditGalaxy.name, EditGalaxy.right_ascension, EditGalaxy.declination, EditGalaxy.coordinate_system, EditGalaxy.lensing_flag, EditGalaxy.classification, EditGalaxy.notes, EditGalaxy.original_id).filter(EditGalaxy.id==id).all()
            g = Galaxy (name = galaxy[0][0], right_ascension = galaxy[0][1], declination = galaxy[0][2], coordinate_system = galaxy[0][3], lensing_flag = galaxy [0][4], classification = galaxy[0][5], notes = galaxy [0][6])
            original_id = galaxy [0][7]
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            existed = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == id).update({TempLine.from_existed_id: existed})
            g_temp = EditGalaxy.query.filter_by(id=id).first()
            db.session.delete (g_temp)
            db.session.commit ()
            oldg  = Galaxy.query.filter_by(name = original_id).first()
            db.session.delete(oldg)
            db.session.commit ()
            flash ("Galaxy has been Edited")            
        
    @action('check for similar', 'Check For Similar')
    def action_check_for_similar(self, ids):
        session=Session()
        for id in ids:
            galaxy = session.query(EditGalaxy).filter(EditGalaxy.id == id)
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

            session.query(EditGalaxy).filter(EditGalaxy.id==id).update({"admin_notes": similar_galaxy_name})
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

class EditLineView(ModelView):
    #details_template = "/admin/model/templine.html"
    #list_template = "/admin/model/templine.html"
    #@expose('/templine/')
    #def templine(self):
        #return self.render('/admin/model/templine.html')

    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            line = session.query(EditLine.galaxy_id, EditLine.j_upper, EditLine.integrated_line_flux, EditLine.integrated_line_flux_uncertainty_positive, EditLine.integrated_line_flux_uncertainty_negative, EditLine.peak_line_flux, EditLine.peak_line_flux_uncertainty_positive, EditLine.peak_line_flux_uncertainty_negative, EditLine.line_width, EditLine.line_width_uncertainty_positive, EditLine.line_width_uncertainty_negative, EditLine.observed_line_frequency, EditLine.observed_line_frequency_uncertainty_positive, EditLine.observed_line_frequency_uncertainty_negative, EditLine.detection_type, EditLine.observed_beam_major, EditLine.observed_beam_minor, EditLine.observed_beam_angle, EditLine.reference, EditLine.notes, EditLine.from_existed_id).filter(EditLine.id==id).all()
            if (line [0][20] == None):
                raise Exception('You have not yet approved the galaxy to whoch the line belongs to')
            else:
                g_id = line [0][20]
            l = Line (galaxy_id = g_id, j_upper = line [0][1], integrated_line_flux = line [0][2], integrated_line_flux_uncertainty_positive = line [0][3], integrated_line_flux_uncertainty_negative = line [0][4], peak_line_flux = line [0][5], peak_line_flux_uncertainty_positive = line [0][6], peak_line_flux_uncertainty_negative = line [0][7], line_width = line [0][8], line_width_uncertainty_positive = line [0][9], line_width_uncertainty_negative = line [0][10], observed_line_frequency = line [0][11], observed_line_frequency_uncertainty_positive = line [0][12], observed_line_frequency_uncertainty_negative = line [0][13], detection_type = line [0][14], observed_beam_major = line [0][15], observed_beam_minor = line [0][16], observed_beam_angle = line [0][17], reference = line [0][18], notes = line [0][19])
            db.session.add (l)
            total = update_redshift(session, g_id)
            update_redshift_error(session, g_id, total)
            db.session.commit ()
            l_temp = EditLine.query.filter_by(id=id).first()
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
        session = Session()
        posts_query = session.query(Post).all()
        return self.render("/admin/posts.html", posts_query=posts_query)
    

class AdminView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next = request.url))
    
class UserView(AdminView):
    @action('make admin',
        'Make Admin',
        'Are you sure you want to give this user admin privileges?')
    def action_make_admin(self, ids):
        for id in ids:
            user = db.session.query(User).filter(User.id==id).first()
            has_role = user_datastore.add_role_to_user(user=user, role='admin')
            db.session.add(user)
            db.session.commit()
    @action('make member',
        'Make Member',
        'Are you sure you want to delete this user\'s privileges?')
    def action_make_member(self, ids):
        for id in ids:
            user = db.session.query(User).filter(User.id==id).first()
            has_role = user_datastore.remove_role_from_user(user=user, role='admin')
            db.session.add(user)
            db.session.commit()







admin.add_view(UserView(User, db.session))
admin.add_view(AdminView(Role, db.session))
admin.add_view(AdminView(Galaxy, db.session))
admin.add_view(AdminView(Line, db.session))
admin.add_view(PostsView(name='Posts', endpoint='posts'))
admin.add_view(AdminView(Post, db.session))
admin.add_view(TempGalaxyView (TempGalaxy, db.session, category = "New Entries"))
admin.add_view(TempLineView(TempLine, db.session, category = "New Entries"))
admin.add_view(EditGalaxyView (EditGalaxy, db.session, category = "New Edits"))
admin.add_view(EditLineView (EditLine, db.session, category = "New Edits"))






