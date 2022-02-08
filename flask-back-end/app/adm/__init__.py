from flask import (
    Blueprint,
    url_for,
    redirect,
    flash,
    request,
    jsonify,
    render_template
)
from flask_admin.contrib.sqla import ModelView
from flask_admin import (
    expose,
    BaseView
)
from flask_admin.actions import action
from flask_admin.contrib.sqla import (
    form,
    filters as sqla_filters,
    tools
)
from flask_login.utils import login_required
from app.models import (
    User,
    Galaxy,
    Line,
    TempGalaxy,
    TempLine,
    Role,
    Post,
    EditGalaxy,
    EditLine
)
from app import (
    db,
    Session,
    admin,
    user_datastore
)
from sqlalchemy import func
from flask_security import current_user
from app.main.routes import (
    within_distance,
    ra_to_float,
    dec_to_float
)
from wtforms.validators import (
    Regexp,
    ValidationError
)
from config import (
    dec_reg_exp,
    ra_reg_exp
)
import json
from datetime import datetime

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

def within_distance(session, query, form_ra, form_dec, distance = 0, based_on_beam_angle = False, temporary = False):
    
    '''
    Takes in a point's coordinates \form_ra and \form_dec and a \distance to check if any galaxy from \query is within the \distance.
    Employs Great-circle distance: https://en.wikipedia.org/wiki/Great-circle_distance
    If the \distance is not provided, it is assumed to be 3 * Line.observed_beam_minor.
    If Line.observed_beam_minor is not available, the distance is assumed to be 5 arcsec to be in an extreme proximity. 

    Returns:
    galaxies -- a query object containing all galaxies that satisfy the distance formula (type::Query). 

    Parameters:
    session -- the session in which the \query is evoked is passed (type::Session).

    query -- predefined query object is passed containing galaxies that are to be considered in terms of their proximity 
    to some point/galaxy with given coordinates. It has to contain the Galaxy & Line table data if the distance is not passed and \based_on_beam_angle == True
    
    form_ra -- right ascension of a point/galaxy
    form_dec -- declination of a point/galaxy
    distance -- circular distance away from the point with coordinates (\form_ra, \form_dec). (default 0)
    based_on_beam_angle -- Boolean value to check whether user wants to search for galaxies with extreme proximity based on their Line.observed_beam_minor.
    (default False)
    temporary -- (type::Boolean), indicator if the check should be performed among not yet approved galaxies (TempGalaxy).
    '''

    if based_on_beam_angle == False:
        galaxies=query.filter(func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < distance)
        return galaxies
    else:
        if temporary == True:
            galaxies = query.filter((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(TempGalaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(TempGalaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - TempGalaxy.declination)))   ) < func.radians(5/3600)) )
        else:
            subqry = session.query(func.max(Line.observed_beam_angle))
            sub = subqry.first()
            sub1 = sub[0]
            if sub1  != None:
                galaxies=query.filter(((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < (func.radians(subqry))/1200) & (subqry != None)) | (func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < func.radians(5/3600)) )   
            else:
                galaxies=query.filter((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < func.radians(5/3600)) )
        return galaxies

def update_right_ascension(galaxy_id):
    session = Session()
    lines = session.query(Line.right_ascension).filter(Line.galaxy_id==galaxy_id).all()
    total = 0
    count = 0
    for line in lines:
        total += line.right_ascension
        count += 1
    if count != 0:
        right_ascension = total / count
        session.query(Galaxy).filter(Galaxy.id==galaxy_id).update({"right_ascension": right_ascension})
        session.commit()
    else: 
        pass
    
def update_declination(galaxy_id):
    session = Session()
    lines = session.query(Line.declination).filter(Line.galaxy_id==galaxy_id).all()
    total = 0
    count = 0
    for line in lines:
        total += line.declination
        count += 1
    if count != 0:
        declination = total / count
        session.query(Galaxy).filter(Galaxy.id==galaxy_id).update({"declination": declination})
        session.commit()
    else: 
        pass

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
            tempgalaxy = TempGalaxy.query.filter(TempGalaxy.id==id).first()
            Galaxy.approve (
                name = tempgalaxy.name,
                right_ascension = tempgalaxy.right_ascension,
                declination = tempgalaxy.declination,
                coordinate_system = tempgalaxy.coordinate_system,
                lensing_flag = tempgalaxy.lensing_flag,
                classification = tempgalaxy.classification,
                notes = tempgalaxy.notes
                )

            from_existed = session.query(func.max(Galaxy.id)).first()
            existed = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == id).update({TempLine.from_existed_id: existed})

            post = Post.query.filter(Post.tempgalaxy_id==id).first()
            db.session.delete(post)
            db.session.commit()

            TempGalaxy.delete_object(tempgalaxy)

            flash ("Galaxy has been Added")            
        

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
            templine = session.query(TempLine).filter(TempLine.id==id).first()
            
            if (templine.from_existed_id == None):
                # line [21] represents TempLine.from_existed_id
                raise Exception('You have not yet approved the galaxy to which the line belongs to')
            else:
                g_id = templine.from_existed_id
            l = Line(galaxy_id = g_id, 
                    emitted_frequency = templine.emitted_frequency, 
                    integrated_line_flux = templine.integrated_line_flux, 
                    integrated_line_flux_uncertainty_positive = templine.integrated_line_flux_uncertainty_positive, 
                    integrated_line_flux_uncertainty_negative = templine.integrated_line_flux_uncertainty_negative, 
                    peak_line_flux = templine.peak_line_flux, 
                    peak_line_flux_uncertainty_positive = templine.peak_line_flux_uncertainty_positive, 
                    peak_line_flux_uncertainty_negative = templine.peak_line_flux_uncertainty_negative, 
                    line_width = templine.line_width, 
                    line_width_uncertainty_positive = templine.line_width_uncertainty_positive, 
                    line_width_uncertainty_negative = templine.line_width_uncertainty_negative, 
                    observed_line_frequency = templine.observed_line_frequency, 
                    observed_line_frequency_uncertainty_positive = templine.observed_line_frequency_uncertainty_positive, 
                    observed_line_frequency_uncertainty_negative = templine.observed_line_frequency_uncertainty_negative, 
                    detection_type = templine.detection_type, 
                    observed_beam_major = templine.observed_beam_major, 
                    observed_beam_minor = templine.observed_beam_minor, 
                    observed_beam_angle = templine.observed_beam_angle, 
                    reference = templine.reference, 
                    notes = templine.notes, 
                    user_submitted = templine.user_submitted, 
                    user_email = templine.user_email, 
                    time_submitted = templine.time_submitted,
                    species = templine.species,
                    right_ascension = templine.right_ascension,
                    declination = templine.declination,
                    approved_username = current_user.username,
                    approved_user_email = current_user.email,
                    approved_time = datetime.utcnow())
            db.session.add (l)
            db.session.commit ()
            total = update_redshift(session, g_id)
            update_redshift_error(session, g_id, total)
            db.session.commit ()
            # Update the coordinates
            update_right_ascension(g_id)
            update_declination(g_id)

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
            line = session.query(EditLine).filter(EditLine.id==id).first()

            original_line_id = line.original_line_id
            galaxy_id = line.galaxy_id

            session.query(Line).filter(
                Line.id == original_line_id
            ).update({"emitted_frequency": line.emitted_frequency, "integrated_line_flux": line.integrated_line_flux, "integrated_line_flux_uncertainty_positive": line.integrated_line_flux_uncertainty_positive, "integrated_line_flux_uncertainty_negative": line.integrated_line_flux_uncertainty_negative, "peak_line_flux": line.peak_line_flux, "peak_line_flux_uncertainty_positive": line.peak_line_flux_uncertainty_positive, "peak_line_flux_uncertainty_negative": line.peak_line_flux_uncertainty_negative, "line_width": line.line_width, "line_width_uncertainty_positive": line.line_width_uncertainty_positive, "line_width_uncertainty_negative": line.line_width_uncertainty_negative, "observed_line_frequency": line.observed_line_frequency, "observed_line_frequency_uncertainty_positive": line.observed_line_frequency_uncertainty_positive, "observed_line_frequency_uncertainty_negative": line.observed_line_frequency_uncertainty_negative, "detection_type": line.detection_type, "observed_beam_major": line.observed_beam_major, "observed_beam_minor": line.observed_beam_minor, "observed_beam_angle": line.observed_beam_angle, "reference": line.reference, "notes": line.notes, "species": line.species})


            total = update_redshift(session, galaxy_id)
            update_redshift_error(session, galaxy_id, total)
            db.session.commit ()

            # Update the coordinates
            update_right_ascension(galaxy_id)
            update_declination(galaxy_id)

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

    @expose('/', methods=['GET', 'POST'])
    def post_view(self):
        if request.method == "POST":
            session = Session()
            data = request.form
            dictionary = data.to_dict(flat=True)
            for key in dictionary.keys():
                dict_of_ids = json.loads(key)
            for key, list_of_ids in dict_of_ids.items():
                if key == 'delete':
                    for id in list_of_ids:
                        id = int(id)
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
                elif key == 'approve':
                    for id in list_of_ids:
                        id = int(id)
                        post = Post.query.filter_by(id=id).first()
                        templine_id = session.query(Post.templine_id).filter_by(id=id).scalar()
                        tempgalaxy_id = session.query(Post.tempgalaxy_id).filter_by(id=id).scalar()
                        editgalaxy_id  = session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
                        editline_id  = session.query(Post.editline_id).filter_by(id=id).scalar()

                        if templine_id != None:
                            
                            templine = TempLine.query.filter_by(id=templine_id).first()
                                
                            if (templine.from_existed_id == None):
                                raise Exception('You have not yet approved the galaxy to which the line belongs to')
                            else:
                                galaxy_id = templine.from_existed_id
                            l = Line (
                                galaxy_id = galaxy_id, 
                                emitted_frequency = templine.emitted_frequency, 
                                integrated_line_flux = templine.integrated_line_flux, 
                                integrated_line_flux_uncertainty_positive = templine.integrated_line_flux_uncertainty_positive, 
                                integrated_line_flux_uncertainty_negative = templine.integrated_line_flux_uncertainty_negative, 
                                peak_line_flux = templine.peak_line_flux, 
                                peak_line_flux_uncertainty_positive = templine.peak_line_flux_uncertainty_positive, 
                                peak_line_flux_uncertainty_negative = templine.peak_line_flux_uncertainty_negative, 
                                line_width = templine.line_width, 
                                line_width_uncertainty_positive = templine.line_width_uncertainty_positive, 
                                line_width_uncertainty_negative = templine.line_width_uncertainty_negative, 
                                observed_line_frequency = templine.observed_line_frequency, 
                                observed_line_frequency_uncertainty_positive = templine.observed_line_frequency_uncertainty_positive, 
                                observed_line_frequency_uncertainty_negative = templine.observed_line_frequency_uncertainty_negative, 
                                detection_type = templine.detection_type, 
                                observed_beam_major = templine.observed_beam_major, 
                                observed_beam_minor = templine.observed_beam_minor, 
                                observed_beam_angle = templine.observed_beam_angle, 
                                reference = templine.reference, 
                                notes = templine.notes, 
                                user_submitted = templine.user_submitted, 
                                user_email = templine.user_email, 
                                time_submitted = templine.time_submitted,
                                species = templine.species,
                                right_ascension = templine.right_ascension,
                                declination = templine.declination,
                                approved_username = current_user.username,
                                approved_user_email = current_user.email,
                                approved_time = datetime.utcnow()
                                )
                            db.session.add (l)
                            db.session.commit ()
                            total = update_redshift(session, galaxy_id)
                            update_redshift_error(session, galaxy_id, total)
                            update_declination(galaxy_id)
                            update_right_ascension(galaxy_id)
                            db.session.delete (templine)
                            db.session.commit ()


                        elif tempgalaxy_id != None:

                            tempgalaxy = TempGalaxy.query.filter(TempGalaxy.id==tempgalaxy_id).first()
                            g = Galaxy (
                                name = tempgalaxy.name,
                                right_ascension = tempgalaxy.right_ascension,
                                declination = tempgalaxy.declination,
                                coordinate_system = tempgalaxy.coordinate_system,
                                lensing_flag = tempgalaxy.lensing_flag,
                                classification = tempgalaxy.classification,
                                notes = tempgalaxy.notes
                                )

                            db.session.add(g)
                            db.session.commit ()
                            from_existed = session.query(func.max(Galaxy.id)).first()
                            existed = from_existed[0]
                            db.session.query(TempLine).filter(TempLine.galaxy_id == tempgalaxy_id).update({TempLine.from_existed_id: existed})
                            db.session.commit()
                            db.session.delete(tempgalaxy)
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
                            update_right_ascension(galaxy_id)
                            update_declination(galaxy_id)
                            #delete the edit
                            db.session.delete(editline)

                        db.session.delete (post)
                        db.session.commit ()  
                elif key == "check":
                    count_of_similar_galaxies = 0
                    dict_of_dict_of_similar = {}
                    for id in list_of_ids:
                        id = int(id)
                        post = Post.query.filter_by(id=id).first()
                        tempgalaxy_id = session.query(Post.tempgalaxy_id).filter_by(id=id).scalar()
                        if tempgalaxy_id == None:
                            continue
                        tempgalaxy = session.query(TempGalaxy).filter_by(id=tempgalaxy_id).first()
                        right_ascension = tempgalaxy.right_ascension
                        declination = tempgalaxy.declination
                    
                        galaxies=session.query(Galaxy, Line).outerjoin(Line)
                        
                        galaxies = within_distance(session, galaxies, right_ascension, declination, based_on_beam_angle=True)
                        galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)
                        dict_of_similar = {'similar_id': '', 'similar_name': '', 'similar_ra': '', 'similar_dec': '', 'investigated_id': '', 'investigated_name': '', 'investigated_ra': '', 'investigated_dec': ''}
                        similar_galaxy = galaxies.first()
                        if similar_galaxy != None:
                            count_of_similar_galaxies += 1
                            similar_id = str(similar_galaxy[0].id)
                            similar_name = str(similar_galaxy[0].name)
                            similar_ra = str(similar_galaxy[0].right_ascension)
                            similar_dec = str(similar_galaxy[0].declination)
                            investigated_id = str(tempgalaxy.id)
                            investigated_name = str(tempgalaxy.name)
                            investigated_ra = str(tempgalaxy.right_ascension)
                            investigated_dec = str(tempgalaxy.declination)
                            list_of_values = [similar_id, similar_name, similar_ra, similar_dec, investigated_id, investigated_name, investigated_ra, investigated_dec]
                            dict_of_similar = dict(zip(dict_of_similar, list_of_values))
                            dict_of_dict_of_similar[count_of_similar_galaxies] = dict_of_similar
                    return render_template('home.html', title= 'Test Home')


        session = Session()
        count_of_similar_galaxies = 0
        dict_of_dict_of_similar = {}
        list_of_tempgalaxy_ids = []
        posts_of_galaxies = session.query(Post).filter(Post.tempgalaxy_id != None).all()
        for query in posts_of_galaxies:
            list_of_tempgalaxy_ids.append(query.tempgalaxy_id)
        for id in list_of_tempgalaxy_ids:
            id = int(id)
            tempgalaxy = session.query(TempGalaxy).filter_by(id=id).first()
            right_ascension = tempgalaxy.right_ascension
            declination = tempgalaxy.declination


        
            galaxies=session.query(Galaxy, Line).outerjoin(Line)
            
            galaxies = within_distance(session, galaxies, right_ascension, declination, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)

            tempgalaxies=session.query(TempGalaxy)
            tempgalaxies=within_distance(session, tempgalaxies, right_ascension, declination, based_on_beam_angle=True, temporary=True)

            similar_galaxy = galaxies.first()
            similar_tempgalaxy = tempgalaxies.first()

            if similar_galaxy != None:
                dict_of_similar = {'similar_id': '', 'similar_name': '', 'similar_ra': '', 'similar_dec': '', 'similar_lines_approved': '', 'similar_lines_waiting_approval': '', 'investigated_id': '', 'investigated_name': '', 'investigated_ra': '', 'investigated_dec': '', 'investigated_lines_approved': '', 'investigated_lines_waiting_approval': '', 'relationship': ''}

                count_of_similar_galaxies += 1
                similar_id = str(similar_galaxy[0].id)
                similar_name = str(similar_galaxy[0].name)
                similar_ra = str(similar_galaxy[0].right_ascension)
                similar_dec = str(similar_galaxy[0].declination)
                investigated_id = str(tempgalaxy.id)
                investigated_name = str(tempgalaxy.name)
                investigated_ra = str(tempgalaxy.right_ascension)
                investigated_dec = str(tempgalaxy.declination)
                # Lines count
                similar_lines_waiting_approval_count = 0
                similar_lines_approved_count = 0
                investigated_lines_waiting_approval_count = 0
                investigated_lines_approved_count = 0

                investigated_lines_waiting_approval_count = session.query(func.count(TempLine.id)).filter(TempLine.galaxy_id==id).scalar()
                similar_lines_approved_count = session.query(func.count(Line.id)).filter(Line.galaxy_id==int(similar_id)).scalar()
                similar_lines_waiting_approval_count = session.query(func.count(TempLine.id)).filter(TempLine.from_existed_id==int(similar_id)).scalar()
                
                list_of_values = [similar_id, similar_name, similar_ra, similar_dec, similar_lines_approved_count, similar_lines_waiting_approval_count,  investigated_id, investigated_name, investigated_ra, investigated_dec, investigated_lines_approved_count, investigated_lines_waiting_approval_count, 'approved_temp']
                dict_of_similar = dict(zip(dict_of_similar, list_of_values))
                dict_of_dict_of_similar[count_of_similar_galaxies] = dict_of_similar
            
            if (similar_tempgalaxy != None) & (similar_tempgalaxy.id != tempgalaxy.id):
                dict_of_similar = {'similar_id': '', 'similar_name': '', 'similar_ra': '', 'similar_dec': '', 'similar_lines_approved': '', 'similar_lines_waiting_approval': '', 'investigated_id': '', 'investigated_name': '', 'investigated_ra': '', 'investigated_dec': '', 'investigated_lines_approved': '', 'investigated_lines_waiting_approval': '', 'relationship': ''}

                count_of_similar_galaxies += 1
                similar_id = str(similar_tempgalaxy.id)
                similar_name = str(similar_tempgalaxy.name)
                similar_ra = str(similar_tempgalaxy.right_ascension)
                similar_dec = str(similar_tempgalaxy.declination)
                investigated_id = str(tempgalaxy.id)
                investigated_name = str(tempgalaxy.name)
                investigated_ra = str(tempgalaxy.right_ascension)
                investigated_dec = str(tempgalaxy.declination)
                # Lines count
                similar_lines_waiting_approval_count = 0
                similar_lines_approved_count = 0
                investigated_lines_waiting_approval_count = 0
                investigated_lines_approved_count = 0

                investigated_lines_waiting_approval_count = session.query(func.count(TempLine.id)).filter(TempLine.galaxy_id==id).scalar()
                similar_lines_waiting_approval_count = session.query(func.count(TempLine.id)).filter(TempLine.galaxy_id==int(similar_id)).scalar()
                
                list_of_values = [similar_id, similar_name, similar_ra, similar_dec, similar_lines_approved_count, similar_lines_waiting_approval_count,  investigated_id, investigated_name, investigated_ra, investigated_dec, investigated_lines_approved_count, investigated_lines_waiting_approval_count, 'temp_temp']
                dict_of_similar = dict(zip(dict_of_similar, list_of_values))
                dict_of_dict_of_similar[count_of_similar_galaxies] = dict_of_similar

        

        posts_query = session.query(Post, TempGalaxy, TempLine, EditGalaxy, EditLine).select_from(Post).outerjoin(TempGalaxy, TempGalaxy.id == Post.tempgalaxy_id).outerjoin(TempLine, TempLine.id == Post.templine_id).outerjoin(EditGalaxy, EditGalaxy.id == Post.editgalaxy_id).outerjoin(EditLine, EditLine.id == Post.editline_id).all()
        #return self.render("/test_dump.html", posts_query=posts_query)
        return self.render("/admin/posts.html", posts_query=posts_query, dict_of_dict_of_similar=dict_of_dict_of_similar, count_of_similar_galaxies=count_of_similar_galaxies)


@bp.route('/resolve/<main_id>/<other_id>/<type>/<relationship>', methods=["GET", "POST"])
@login_required
def resolve(main_id, other_id, type, relationship):
    main_id = int(main_id)
    other_id = int(other_id)
    session = Session()

    if relationship == 'approved_temp':
        if type == "similar_to_investigated":

            # Approve the galaxy first
            tempgalaxy = TempGalaxy.query.filter_by(id=main_id).first()
            post = Post.query.filter_by(tempgalaxy_id=main_id).first()

            galaxy = session.query(TempGalaxy.name, TempGalaxy.right_ascension, TempGalaxy.declination, TempGalaxy.coordinate_system, TempGalaxy.lensing_flag, TempGalaxy.classification, TempGalaxy.notes).filter(TempGalaxy.id==main_id).first()
            g = Galaxy (name = galaxy[0], right_ascension = galaxy[1], declination = galaxy[2], coordinate_system = galaxy[3], lensing_flag = galaxy [4], classification = galaxy[5], notes = galaxy [6])
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            existed = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == main_id).update({TempLine.from_existed_id: existed})
            db.session.commit()
            db.session.delete (tempgalaxy)
            db.session.commit()
            db.session.delete(post)
            db.session.commit()
            
            # Reassign temporary lines to the newly approved galaxy. 
            lines = session.query(Line).filter(Line.galaxy_id==other_id).all()
            for line in lines:
                line.galaxy_id = existed

            # Delete old approved galaxy
            old_galaxy = session.query(Galaxy).filter_by(id=other_id).first()
            db.session.delete(old_galaxy)
            db.session.commit()

        elif type == "investigated_to_similar":

            db.session.query(TempLine).filter(TempLine.galaxy_id == other_id).update({TempLine.from_existed_id: main_id})
            db.session.commit()
            tempgalaxy = TempGalaxy.query.filter_by(id=other_id).first()
            db.session.delete(tempgalaxy)
            db.session.commit()

        elif type == "different":
            # Approve temporary first
            post = Post.query.filter_by(tempgalaxy_id=other_id).first()
            galaxy = TempGalaxy.query.filter(TempGalaxy.id==other_id).first()
            g = Galaxy (name = galaxy.name, right_ascension = galaxy.right_ascension, declination = galaxy.declination, coordinate_system = galaxy.coordinate_system, lensing_flag = galaxy.lensing_flag, classification = galaxy.classification, notes = galaxy.notes)
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            existed = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == main_id).update({TempLine.from_existed_id: existed})
            db.session.commit()
            db.session.delete(galaxy)
            db.session.commit()
            db.session.delete(post)
            db.session.commit()
            # Remember similarity
            galaxy_2_id = existed
            galaxy_1_id = main_id
            db.session.query(Galaxy).filter(Galaxy.id == galaxy_1_id).update({Galaxy.is_similar: galaxy_2_id})
            db.session.commit()
            db.session.query(Galaxy).filter(Galaxy.id == galaxy_2_id).update({Galaxy.is_similar: galaxy_1_id})
            db.session.commit()
    
    elif relationship == 'temp_temp':
        if type == "different":
            # Approve both galaxies
            # 1
            galaxy = TempGalaxy.query.filter(TempGalaxy.id==other_id).first()
            post = Post.query.filter_by(tempgalaxy_id=other_id).first()
            g = Galaxy (name = galaxy.name, right_ascension = galaxy.right_ascension, declination = galaxy.declination, coordinate_system = galaxy.coordinate_system, lensing_flag = galaxy.lensing_flag, classification = galaxy.classification, notes = galaxy.notes)
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            galaxy_1_id = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == other_id).update({TempLine.from_existed_id: galaxy_1_id})
            db.session.commit()
            db.session.delete(galaxy)
            db.session.commit()
            db.session.delete(post)
            db.session.commit()
            # 2
            galaxy = TempGalaxy.query.filter(TempGalaxy.id==main_id).first()
            post = Post.query.filter_by(tempgalaxy_id=main_id).first()
            g = Galaxy (name = galaxy.name, right_ascension = galaxy.right_ascension, declination = galaxy.declination, coordinate_system = galaxy.coordinate_system, lensing_flag = galaxy.lensing_flag, classification = galaxy.classification, notes = galaxy.notes)
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            galaxy_2_id = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == main_id).update({TempLine.from_existed_id: galaxy_2_id})
            db.session.commit()
            db.session.delete(galaxy)
            db.session.commit()
            db.session.delete(post)
            db.session.commit()

            # Remember similarity
            db.session.query(Galaxy).filter(Galaxy.id == galaxy_1_id).update({Galaxy.is_similar: galaxy_2_id})
            db.session.commit()
            db.session.query(Galaxy).filter(Galaxy.id == galaxy_2_id).update({Galaxy.is_similar: galaxy_1_id})
            db.session.commit()

        else:
            main = TempGalaxy.query.filter_by(id=main_id).first()
            post_of_main = Post.query.filter_by(tempgalaxy_id=main_id).first()
            other = TempGalaxy.query.filter_by(id=other_id).first()
            post_of_other = Post.query.filter_by(tempgalaxy_id=other_id).first()

            # Approve main
            galaxy = session.query(TempGalaxy.name, TempGalaxy.right_ascension, TempGalaxy.declination, TempGalaxy.coordinate_system, TempGalaxy.lensing_flag, TempGalaxy.classification, TempGalaxy.notes).filter(TempGalaxy.id==main_id).first()
            g = Galaxy (name = galaxy[0], right_ascension = galaxy[1], declination = galaxy[2], coordinate_system = galaxy[3], lensing_flag = galaxy [4], classification = galaxy[5], notes = galaxy [6])
            db.session.add (g)
            db.session.commit ()
            from_existed = session.query(func.max(Galaxy.id)).first()
            existed = from_existed[0]
            db.session.query(TempLine).filter(TempLine.galaxy_id == main_id).update({TempLine.from_existed_id: existed})
            db.session.commit()
            db.session.delete (main)
            db.session.commit()
            db.session.delete(post_of_main)
            db.session.commit()

            # Reassign temporary lines to the newly approved galaxy. 
            lines = session.query(TempLine).filter(TempLine.galaxy_id==other_id).all()
            for line in lines:
                line.from_existed_id = existed

            # Delete other tempgalaxy
            db.session.delete(other)
            db.session.commit()
            db.session.delete(post_of_other)
            db.session.commit()

        

    return redirect("/posts")

    #@action('delete',
     ##      'Are you sure you want to delete selected records?')
    #def action_delete(self, ids)


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

        line = session.query(TempLine.galaxy_id, TempLine.emitted_frequency, TempLine.integrated_line_flux, TempLine.integrated_line_flux_uncertainty_positive, TempLine.integrated_line_flux_uncertainty_negative, TempLine.peak_line_flux, TempLine.peak_line_flux_uncertainty_positive, TempLine.peak_line_flux_uncertainty_negative, TempLine.line_width, TempLine.line_width_uncertainty_positive, TempLine.line_width_uncertainty_negative, TempLine.observed_line_frequency, TempLine.observed_line_frequency_uncertainty_positive, TempLine.observed_line_frequency_uncertainty_negative, TempLine.detection_type, TempLine.observed_beam_major, TempLine.observed_beam_minor, TempLine.observed_beam_angle, TempLine.reference, TempLine.notes, TempLine.from_existed_id, TempLine.user_submitted, TempLine.user_email, TempLine.time_submitted, TempLine.species).filter(TempLine.id==templine_id).first()
            
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






