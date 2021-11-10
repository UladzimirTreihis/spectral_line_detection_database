from flask import Blueprint, url_for, redirect, flash, request
from flask.cli import with_appcontext
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, expose, BaseView, AdminIndexView
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.actions import action
from flask_admin.contrib.sqla import form, filters as sqla_filters, tools
from flask_login.utils import login_required
from sqlalchemy.orm import session, aliased
from sqlalchemy.sql import alias
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
            Line.emitted_frequency, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
        ).outerjoin(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).all() 

    sum_upper = sum_lower = 0
    for l in line_redshift:
        if (l.observed_line_frequency_uncertainty_positive == None) or (l.observed_line_frequency == None):
            continue
        if l.observed_line_frequency_uncertainty_negative == None:
            delta_nu = 2 * l.observed_line_frequency_uncertainty_positive
        else:
            delta_nu = l.observed_line_frequency_uncertainty_positive + l.observed_line_frequency_uncertainty_negative

        z = (l.emitted_frequency - l.observed_line_frequency) / l.observed_line_frequency
        delta_z = ((1 + z) * delta_nu) / l.observed_line_frequency
        sum_upper = sum_upper =+ (z/delta_z)
        sum_lower = sum_lower =+ (1/delta_z)
    #This case passes -1 to change redshift error, which will signal that no change needed
    if sum_lower == 0:
        return -1

    redshift_weighted = sum_upper / sum_lower
    session.query(Galaxy).filter(
        Galaxy.id == galaxy_id
    ).update({"redshift": redshift_weighted})
    session.commit()
    
    return sum_upper

def update_redshift_error(session, galaxy_id, sum_upper):
    if sum_upper != -1:

        redshift_error_weighted = 0
        line_redshift = session.query(
                Line.emitted_frequency, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
            ).outerjoin(Galaxy).filter(
                Galaxy.id == galaxy_id
            ).all() 
        for l in line_redshift:
            if (l.observed_line_frequency_uncertainty_positive == None) or (l.observed_line_frequency == None):
                continue
            if l.observed_line_frequency_uncertainty_negative == None:
                delta_nu = 2 * l.observed_line_frequency_uncertainty_positive
            else:
                delta_nu = l.observed_line_frequency_uncertainty_positive + l.observed_line_frequency_uncertainty_negative

            z = (l.emitted_frequency - l.observed_line_frequency) / l.observed_line_frequency
            delta_z = ((1 + z) * delta_nu) / l.observed_line_frequency
            weight = (z/delta_z)/sum_upper
            redshift_error_weighted = redshift_error_weighted =+ (weight*delta_z)
        if redshift_error_weighted != 0:
            session.query(Galaxy).filter(
                Galaxy.id == galaxy_id
            ).update({"redshift_error": redshift_error_weighted})
            session.commit()

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
    @action('delete',
           'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):

        #deletes the corresponding post
        for id in ids:
            post = Post.query.filter(Post.tempgalaxy_id==id).first()
            db.session.delete(post)
            db.session.commit()

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

    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            galaxy = session.query(TempGalaxy.name, TempGalaxy.right_ascension, TempGalaxy.declination, TempGalaxy.coordinate_system, TempGalaxy.lensing_flag, TempGalaxy.classification, TempGalaxy.notes).filter(TempGalaxy.id==id).first()
            g = Galaxy (name = galaxy[0], right_ascension = galaxy[1], declination = galaxy[2], coordinate_system = galaxy[3], lensing_flag = galaxy [4], classification = galaxy[5], notes = galaxy [6])
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            existed = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == id).update({TempLine.from_existed_id: existed})
            g_temp = TempGalaxy.query.filter_by(id=id).first()

            post = Post.query.filter(Post.tempgalaxy_id==id).first()
            db.session.delete(post)
            db.session.commit()

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
            galaxy = session.query(EditGalaxy.name, EditGalaxy.right_ascension, EditGalaxy.declination, EditGalaxy.coordinate_system, EditGalaxy.lensing_flag, EditGalaxy.classification, EditGalaxy.notes, EditGalaxy.original_id).filter(EditGalaxy.id==id).first()
            original_id = galaxy [7]

            session.query(Galaxy).filter(
                Galaxy.id == original_id
            ).update({"name": galaxy[0], "right_ascension": galaxy[1], "declination": galaxy[2], "coordinate_system": galaxy[3], "lensing_flag": galaxy[4], "classification": galaxy[5], "notes": galaxy[6]})
            session.commit()
            g_edit = EditGalaxy.query.filter_by(id=id).first()

            post = Post.query.filter(Post.editgalaxy_id==id).first()
            db.session.delete(post)
            db.session.commit()

            db.session.delete (g_edit)
            db.session.commit ()

            flash ("Galaxy has been Edited")     

    @action('delete',
           'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):

        for id in ids:
            post = Post.query.filter(Post.editgalaxy_id==id).first()
            db.session.delete(post)
            db.session.commit()

        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        if self.fast_mass_delete:
            count = query.delete(synchronize_session=False)
        else:
            count = 0
            for m in query.all():
                if self.delete_model(m):
                    count += 1
        self.session.commit()       
        
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
            line = session.query(TempLine.galaxy_id, TempLine.emitted_frequency, TempLine.species, TempLine.integrated_line_flux, TempLine.integrated_line_flux_uncertainty_positive, TempLine.integrated_line_flux_uncertainty_negative, TempLine.peak_line_flux, TempLine.peak_line_flux_uncertainty_positive, TempLine.peak_line_flux_uncertainty_negative, TempLine.line_width, TempLine.line_width_uncertainty_positive, TempLine.line_width_uncertainty_negative, TempLine.observed_line_frequency, TempLine.observed_line_frequency_uncertainty_positive, TempLine.observed_line_frequency_uncertainty_negative, TempLine.detection_type, TempLine.observed_beam_major, TempLine.observed_beam_minor, TempLine.observed_beam_angle, TempLine.reference, TempLine.notes, TempLine.from_existed_id, TempLine.user_submitted, TempLine.user_email, TempLine.admin_notes, TempLine.time_submitted).filter(TempLine.id==id).first()
            
            if (line [21] == None):
                # line [21] represents TempLine.from_existed_id
                raise Exception('You have not yet approved the galaxy to which the line belongs to')
            else:
                g_id = line [21]
            l = Line (galaxy_id = g_id, emitted_frequency = line [1], species = line [2], integrated_line_flux = line [3], integrated_line_flux_uncertainty_positive = line [4], integrated_line_flux_uncertainty_negative = line [5], peak_line_flux = line [6], peak_line_flux_uncertainty_positive = line [7], peak_line_flux_uncertainty_negative = line [8], line_width = line [9], line_width_uncertainty_positive = line [10], line_width_uncertainty_negative = line [11], observed_line_frequency = line [12], observed_line_frequency_uncertainty_positive = line [13], observed_line_frequency_uncertainty_negative = line [14], detection_type = line [15], observed_beam_major = line [16], observed_beam_minor = line [17], observed_beam_angle = line [18], reference = line [19], notes = line [20], user_submitted = line [22], user_email = line[23])
            db.session.add (l)
            db.session.commit ()
            total = update_redshift(session, g_id)
            update_redshift_error(session, g_id, total)
            db.session.commit ()
            #delete the corresponding post
            post = Post.query.filter(Post.templine_id==id).first()
            db.session.delete(post)
            db.session.commit ()
            #delete the corresponding line
            l_temp = TempLine.query.filter_by(id=id).first()
            db.session.delete (l_temp)
            db.session.commit ()

    @action('delete',
           'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):
        
        session = Session ()
        #deletes the corresponding post
        for id in ids:
            post = Post.query.filter(Post.templine_id==id).first()
            db.session.delete(post)
            db.session.commit ()

        #deletes the corresponding temporary line
        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        if self.fast_mass_delete:
            count = query.delete(synchronize_session=False)
        else:
            count = 0
            for m in query.all():
                if self.delete_model(m):
                    count += 1
        self.session.commit()

        flash('Record was successfully deleted.')

class EditLineView(ModelView):

    @action('approve', 'Approve')
    def action_approve(self, ids):
        session = Session ()
        for id in ids:
            line = session.query(EditLine.galaxy_id, EditLine.original_line_id, EditLine.emitted_frequency, EditLine.integrated_line_flux, EditLine.integrated_line_flux_uncertainty_positive, EditLine.integrated_line_flux_uncertainty_negative, EditLine.peak_line_flux, EditLine.peak_line_flux_uncertainty_positive, EditLine.peak_line_flux_uncertainty_negative, EditLine.line_width, EditLine.line_width_uncertainty_positive, EditLine.line_width_uncertainty_negative, EditLine.observed_line_frequency, EditLine.observed_line_frequency_uncertainty_positive, EditLine.observed_line_frequency_uncertainty_negative, EditLine.detection_type, EditLine.observed_beam_major, EditLine.observed_beam_minor, EditLine.observed_beam_angle, EditLine.reference, EditLine.notes, EditLine.species).filter(EditLine.id==id).first()

            original_line_id = line[1]
            galaxy_id = line[0]

            session.query(Line).filter(
                Line.id == original_line_id
            ).update({"emitted_frequency": line[2], "integrated_line_flux": line[3], "integrated_line_flux_uncertainty_positive": line[4], "integrated_line_flux_uncertainty_negative": line[5], "peak_line_flux": line[6], "peak_line_flux_uncertainty_positive": line[7], "peak_line_flux_uncertainty_negative": line[8], "line_width": line[9], "line_width_uncertainty_positive": line[10], "line_width_uncertainty_negative": line[11], "observed_line_frequency": line[12], "observed_line_frequency_uncertainty_positive": line[13], "observed_line_frequency_uncertainty_negative": line[14], "detection_type": line[15], "observed_beam_major": line[16], "observed_beam_minor": line[17], "observed_beam_angle": line[18], "reference": line[19], "notes": line[20], "species": line[21]})


            total = update_redshift(session, galaxy_id)
            update_redshift_error(session, galaxy_id, total)
            db.session.commit ()

            #deletes the corresponding post
            post = Post.query.filter(Post.editline_id==id).first()
            db.session.delete(post)
            db.session.commit()

            #deletes the edit
            l_edit = EditLine.query.filter_by(id=id).first()
            db.session.delete (l_edit)
            db.session.commit ()


    @action('delete',
           'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):

        for id in ids:
            post = Post.query.filter(Post.editline_id==id).first()
            db.session.delete(post)
            db.session.commit()

        query = tools.get_query_for_ids(self.get_query(), self.model, ids)
        if self.fast_mass_delete:
            count = query.delete(synchronize_session=False)
        else:
            count = 0
            for m in query.all():
                if self.delete_model(m):
                    count += 1
        self.session.commit()

        flash('Record was successfully deleted.')

class PostsView(BaseView):

    @expose('/')
    def post_view(self):
        session = Session()
 
        posts_query = session.query(Post, TempGalaxy, TempLine, EditGalaxy, EditLine).select_from(Post).outerjoin(TempGalaxy, TempGalaxy.id == Post.tempgalaxy_id).outerjoin(TempLine, TempLine.id == Post.templine_id).outerjoin(EditGalaxy, EditGalaxy.id == Post.editgalaxy_id).outerjoin(EditLine, EditLine.id == Post.editline_id).all()
        #return self.render("/test_dump.html", posts_query=posts_query)
        return self.render("/admin/posts.html", posts_query=posts_query)

    #@action('delete',
     ##      'Are you sure you want to delete selected records?')
    #def action_delete(self, ids)


@bp.route('/posts_delete/<ids>') 
@login_required  
def posts_delete(ids):

    '''
    Deletes the submission (unapproved) from the entire db.
    Used by admin/posts.
    
    '''
    entries = request.form.getlist('rowid')
    session = Session()
    post = Post.query.filter_by(id=id).first()
    templine_id = session.query(Post.templine_id).filter_by(id=id).scalar()
    tempgalaxy_id = session.query(Post.tempgalaxy_id).filter_by(id=id).scalar()
    editgalaxy_id  = session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
    editline_id  = session.query(Post.editline_id).filter_by(id=id).scalar()
    if templine_id != None:
        templine = TempLine.query.filter_by(id=templine_id).first()
        db.session.delete (templine)
    elif tempgalaxy_id != None:
        tempgalaxy = TempGalaxy.query.filter_by(id=tempgalaxy_id).first()
        db.session.delete (tempgalaxy)
    elif editgalaxy_id != None:
        editgalaxy = EditGalaxy.query.filter_by(id=editgalaxy_id).first()
        db.session.delete(editgalaxy)
    else:
        editline = EditLine.query.filter_by(id=editline_id).first()
        db.session.delete(editline)
    db.session.delete (post)
    db.session.commit ()    
    return redirect("/posts")

@bp.route('/post_delete/<id>') 
@login_required  
def post_delete(id):
    '''
    Deletes the submission (unapproved) from the entire db.
    Used by admin/posts.
    
    '''
    session = Session()
    post = Post.query.filter_by(id=id).first()
    templine_id = session.query(Post.templine_id).filter_by(id=id).scalar()
    tempgalaxy_id = session.query(Post.tempgalaxy_id).filter_by(id=id).scalar()
    editgalaxy_id  = session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
    editline_id  = session.query(Post.editline_id).filter_by(id=id).scalar()
    if templine_id != None:
        templine = TempLine.query.filter_by(id=templine_id).first()
        db.session.delete (templine)
    elif tempgalaxy_id != None:
        tempgalaxy = TempGalaxy.query.filter_by(id=tempgalaxy_id).first()
        db.session.delete (tempgalaxy)
    elif editgalaxy_id != None:
        editgalaxy = EditGalaxy.query.filter_by(id=editgalaxy_id).first()
        db.session.delete(editgalaxy)
    else:
        editline = EditLine.query.filter_by(id=editline_id).first()
        db.session.delete(editline)
    db.session.delete (post)
    db.session.commit ()    
    return redirect("/posts")


@bp.route('/post_approve/<id>') 
@login_required  
def post_approve(id):
    '''
    Approves the submission.
    Used by admin/posts.
    
    '''
    session = Session()
    post = Post.query.filter_by(id=id).first()
    templine_id = session.query(Post.templine_id).filter_by(id=id).scalar()
    tempgalaxy_id = session.query(Post.tempgalaxy_id).filter_by(id=id).scalar()
    editgalaxy_id  = session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
    editline_id  = session.query(Post.editline_id).filter_by(id=id).scalar()

    if templine_id != None:
        
        templine = TempLine.query.filter_by(id=templine_id).first()

        line = session.query(TempLine.galaxy_id, TempLine.emitted_frequency, TempLine.integrated_line_flux, TempLine.integrated_line_flux_uncertainty_positive, TempLine.integrated_line_flux_uncertainty_negative, TempLine.peak_line_flux, TempLine.peak_line_flux_uncertainty_positive, TempLine.peak_line_flux_uncertainty_negative, TempLine.line_width, TempLine.line_width_uncertainty_positive, TempLine.line_width_uncertainty_negative, TempLine.observed_line_frequency, TempLine.observed_line_frequency_uncertainty_positive, TempLine.observed_line_frequency_uncertainty_negative, TempLine.detection_type, TempLine.observed_beam_major, TempLine.observed_beam_minor, TempLine.observed_beam_angle, TempLine.reference, TempLine.notes, TempLine.from_existed_id, TempLine.user_submitted, TempLine.user_email, TempLine.admin_notes, TempLine.time_submitted, TempLine.species).filter(TempLine.id==templine_id).first()
            
        if (line [20] == None):
            # line [20] represents TempLine.from_existed_id
            raise Exception('You have not yet approved the galaxy to which the line belongs to')
        else:
            g_id = line [20]
        l = Line (galaxy_id = g_id, emitted_frequency = line [1], integrated_line_flux = line [2], integrated_line_flux_uncertainty_positive = line [3], integrated_line_flux_uncertainty_negative = line [4], peak_line_flux = line [5], peak_line_flux_uncertainty_positive = line [6], peak_line_flux_uncertainty_negative = line [7], line_width = line [8], line_width_uncertainty_positive = line [9], line_width_uncertainty_negative = line [10], observed_line_frequency = line [11], observed_line_frequency_uncertainty_positive = line [12], observed_line_frequency_uncertainty_negative = line [13], detection_type = line [14], observed_beam_major = line [15], observed_beam_minor = line [16], observed_beam_angle = line [17], reference = line [18], notes = line [19], user_submitted = line [21], user_email = line[22], species = line[25])
        db.session.add (l)
        db.session.commit ()
        total = update_redshift(session, g_id)
        update_redshift_error(session, g_id, total)
        db.session.delete (templine)
        db.session.commit ()



    elif tempgalaxy_id != None:

        tempgalaxy = TempGalaxy.query.filter_by(id=tempgalaxy_id).first()

        galaxy = session.query(TempGalaxy.name, TempGalaxy.right_ascension, TempGalaxy.declination, TempGalaxy.coordinate_system, TempGalaxy.lensing_flag, TempGalaxy.classification, TempGalaxy.notes).filter(TempGalaxy.id==tempgalaxy_id).first()

        g = Galaxy (name = galaxy[0], right_ascension = galaxy[1], declination = galaxy[2], coordinate_system = galaxy[3], lensing_flag = galaxy [4], classification = galaxy[5], notes = galaxy [6])
        db.session.add (g)
        db.session.commit ()
        from_existed = session.query(func.max(Galaxy.id)).first()
        existed = from_existed[0]
        db.session.query(TempLine).filter(TempLine.galaxy_id == tempgalaxy_id).update({TempLine.from_existed_id: existed})
        db.session.delete (tempgalaxy)
        db.session.commit()

    elif editgalaxy_id != None:

        editgalaxy = EditGalaxy.query.filter_by(id=editgalaxy_id).first()

        galaxy = session.query(EditGalaxy.name, EditGalaxy.right_ascension, EditGalaxy.declination, EditGalaxy.coordinate_system, EditGalaxy.lensing_flag, EditGalaxy.classification, EditGalaxy.notes, EditGalaxy.original_id).filter(EditGalaxy.id==editgalaxy_id).first()
        original_id = galaxy [7]

        session.query(Galaxy).filter(
            Galaxy.id == original_id
        ).update({"name": galaxy[0], "right_ascension": galaxy[1], "declination": galaxy[2], "coordinate_system": galaxy[3], "lensing_flag": galaxy[4], "classification": galaxy[5], "notes": galaxy[6]})
        db.session.delete(editgalaxy)
        session.commit()


    else:

        editline = EditLine.query.filter_by(id=editline_id).first()
        line = session.query(EditLine.galaxy_id, EditLine.original_line_id, EditLine.emitted_frequency, EditLine.integrated_line_flux, EditLine.integrated_line_flux_uncertainty_positive, EditLine.integrated_line_flux_uncertainty_negative, EditLine.peak_line_flux, EditLine.peak_line_flux_uncertainty_positive, EditLine.peak_line_flux_uncertainty_negative, EditLine.line_width, EditLine.line_width_uncertainty_positive, EditLine.line_width_uncertainty_negative, EditLine.observed_line_frequency, EditLine.observed_line_frequency_uncertainty_positive, EditLine.observed_line_frequency_uncertainty_negative, EditLine.detection_type, EditLine.observed_beam_major, EditLine.observed_beam_minor, EditLine.observed_beam_angle, EditLine.reference, EditLine.notes, EditLine.species).filter(EditLine.id==editline_id).first()

        original_line_id = line[1]
        galaxy_id = line[0]

        session.query(Line).filter(
            Line.id == original_line_id
        ).update({"emitted_frequency": line[2], "integrated_line_flux": line[3], "integrated_line_flux_uncertainty_positive": line[4], "integrated_line_flux_uncertainty_negative": line[5], "peak_line_flux": line[6], "peak_line_flux_uncertainty_positive": line[7], "peak_line_flux_uncertainty_negative": line[8], "line_width": line[9], "line_width_uncertainty_positive": line[10], "line_width_uncertainty_negative": line[11], "observed_line_frequency": line[12], "observed_line_frequency_uncertainty_positive": line[13], "observed_line_frequency_uncertainty_negative": line[14], "detection_type": line[15], "observed_beam_major": line[16], "observed_beam_minor": line[17], "observed_beam_angle": line[18], "reference": line[19], "notes": line[20], "species": line[21]})


        total = update_redshift(session, galaxy_id)
        update_redshift_error(session, galaxy_id, total)
        db.session.commit ()
        #delete the edit
        db.session.delete(editline)

    db.session.delete (post)
    db.session.commit ()    
    return redirect("/posts")


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






