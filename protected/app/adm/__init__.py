from flask import (
    Blueprint,
    session,
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
    EditLine,
    Freq
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
    update_redshift,
    update_redshift_error,
    update_declination,
    update_right_ascension
)
from wtforms.validators import Regexp, ValidationError
from config import dec_reg_exp, ra_reg_exp, template_dir
import json
from datetime import datetime
import csv
from io import TextIOWrapper
from app.main.forms import UploadFileForm
from species import SpeciesNames
from exceptions import SpeciesUnknownError

bp = Blueprint('adm', __name__, template_folder=template_dir + '/admin')


def approve_tempgalaxy(id):
    tempgalaxy = TempGalaxy.query.filter(TempGalaxy.id == id).first()
    Galaxy.approve(
        name=tempgalaxy.name,
        right_ascension=tempgalaxy.right_ascension,
        declination=tempgalaxy.declination,
        coordinate_system=tempgalaxy.coordinate_system,
        lensing_flag=tempgalaxy.lensing_flag,
        classification=tempgalaxy.classification,
        notes=tempgalaxy.notes,
        user_submitted=tempgalaxy.user_submitted,
        user_email=tempgalaxy.user_email,
        time_submitted=tempgalaxy.time_submitted,
        approved_username=current_user.username,
        approved_user_email=current_user.email,
        approved_time=datetime.utcnow()
    )

    from_existed_id = db.session.query(func.max(Galaxy.id)).first()[0]
    db.session.query(TempLine).filter(TempLine.galaxy_id == id).update({TempLine.from_existed_id: from_existed_id})

    post = Post.query.filter(Post.tempgalaxy_id == id).first()
    db.session.delete(post)
    db.session.commit()

    TempGalaxy.delete_object(tempgalaxy)


def approve_templine(id):
    templine = TempLine.query.filter(TempLine.id == id).first()

    if templine.from_existed_id == None:

        flash('You have not yet approved the galaxy to which the line belongs to')
    else:
        galaxy_id = templine.from_existed_id
        l = Line(galaxy_id=galaxy_id,
                 emitted_frequency=templine.emitted_frequency,
                 integrated_line_flux=templine.integrated_line_flux,
                 integrated_line_flux_uncertainty_positive=templine.integrated_line_flux_uncertainty_positive,
                 integrated_line_flux_uncertainty_negative=templine.integrated_line_flux_uncertainty_negative,
                 peak_line_flux=templine.peak_line_flux,
                 peak_line_flux_uncertainty_positive=templine.peak_line_flux_uncertainty_positive,
                 peak_line_flux_uncertainty_negative=templine.peak_line_flux_uncertainty_negative,
                 line_width=templine.line_width,
                 line_width_uncertainty_positive=templine.line_width_uncertainty_positive,
                 line_width_uncertainty_negative=templine.line_width_uncertainty_negative,
                 observed_line_frequency=templine.observed_line_frequency,
                 observed_line_frequency_uncertainty_positive=templine.observed_line_frequency_uncertainty_positive,
                 observed_line_frequency_uncertainty_negative=templine.observed_line_frequency_uncertainty_negative,
                 detection_type=templine.detection_type,
                 observed_beam_major=templine.observed_beam_major,
                 observed_beam_minor=templine.observed_beam_minor,
                 observed_beam_angle=templine.observed_beam_angle,
                 reference=templine.reference,
                 notes=templine.notes,
                 user_submitted=templine.user_submitted,
                 user_email=templine.user_email,
                 time_submitted=templine.time_submitted,
                 species=templine.species,
                 right_ascension=templine.right_ascension,
                 declination=templine.declination,
                 approved_username=current_user.username,
                 approved_user_email=current_user.email,
                 approved_time=datetime.utcnow()
                 )
        db.session.add(l)
        db.session.commit()
        total = update_redshift(galaxy_id)
        update_redshift_error(galaxy_id, total)
        db.session.commit()
        # Update the coordinates
        update_right_ascension(galaxy_id)
        update_declination(galaxy_id)

        # delete the corresponding post
        post = Post.query.filter(Post.templine_id == id).first()
        db.session.delete(post)
        db.session.commit()
        # delete the corresponding templine
        l_temp = TempLine.query.filter_by(id=id).first()
        db.session.delete(l_temp)
        db.session.commit()


def approve_editgalaxy(id):
    editgalaxy = EditGalaxy.query.filter(EditGalaxy.id == id).first()
    original_id = editgalaxy.original_id

    db.session.query(Galaxy).filter(
        Galaxy.id == original_id
    ).update({"name": editgalaxy.name, "coordinate_system": editgalaxy.coordinate_system,
              "lensing_flag": editgalaxy.lensing_flag, "classification": editgalaxy.classification,
              "notes": editgalaxy.classification, "approved_username": current_user.username,
              "approved_user_email": current_user.email, "approved_time": datetime.utcnow()})
    db.session.commit()

    post = Post.query.filter(Post.editgalaxy_id == id).first()
    db.session.delete(post)
    db.session.commit()

    db.session.delete(editgalaxy)
    db.session.commit()


def approve_editline(id):
    editline = EditLine.query.filter(EditLine.id == id).first()

    original_line_id = editline.original_line_id
    galaxy_id = editline.galaxy_id

    db.session.query(Line).filter(
        Line.id == original_line_id
    ).update({"emitted_frequency": editline.emitted_frequency, "integrated_line_flux": editline.integrated_line_flux,
              "integrated_line_flux_uncertainty_positive": editline.integrated_line_flux_uncertainty_positive,
              "integrated_line_flux_uncertainty_negative": editline.integrated_line_flux_uncertainty_negative,
              "peak_line_flux": editline.peak_line_flux,
              "peak_line_flux_uncertainty_positive": editline.peak_line_flux_uncertainty_positive,
              "peak_line_flux_uncertainty_negative": editline.peak_line_flux_uncertainty_negative,
              "line_width": editline.line_width,
              "line_width_uncertainty_positive": editline.line_width_uncertainty_positive,
              "line_width_uncertainty_negative": editline.line_width_uncertainty_negative,
              "observed_line_frequency": editline.observed_line_frequency,
              "observed_line_frequency_uncertainty_positive": editline.observed_line_frequency_uncertainty_positive,
              "observed_line_frequency_uncertainty_negative": editline.observed_line_frequency_uncertainty_negative,
              "detection_type": editline.detection_type, "observed_beam_major": editline.observed_beam_major,
              "observed_beam_minor": editline.observed_beam_minor, "observed_beam_angle": editline.observed_beam_angle,
              "reference": editline.reference, "notes": editline.notes, "species": editline.species,
              "approved_username": current_user.username, "approved_user_email": current_user.email,
              "approved_time": datetime.utcnow()})

    total = update_redshift(galaxy_id)
    update_redshift_error(galaxy_id, total)
    db.session.commit()

    # Update the coordinates
    update_right_ascension(galaxy_id)
    update_declination(galaxy_id)

    # deletes the corresponding post
    post = Post.query.filter(Post.editline_id == id).first()
    db.session.delete(post)
    db.session.commit()

    # deletes the edit
    db.session.delete(editline)
    db.session.commit()


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))


class AdminBaseView(BaseView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))


class GalaxyView(ModelView):
    def check_coords(form, coordinate_system):
        if form.coordinate_system.data != "ICRS" and form.coordinate_system.data != "J2000":
            raise ValidationError('Coordinate System must be either J2000 or ICRS')

    def check_lensing_flag(form, lensing_flag):
        if form.lensing_flag.data != "Lensed" and form.lensing_flag.data != "Unlensed" and form.lensing_flag.data != "Either":
            raise ValidationError('Lensing Flag can only be Lensed, Unlensed or Either')

    form_args = dict(
        coordinate_system=dict(validators=[check_coords]),
        lensing_flag=dict(validators=[check_lensing_flag]),
        right_ascension=dict(validators=[Regexp(ra_reg_exp, message="Input in the format 00h00m00s or as a float")]),
        declination=dict(validators=[Regexp(dec_reg_exp, message="Input in the format (+/-) 00h00m00s or as a float")]),
    )


class TempGalaxyView(ModelView):
    @action('delete',
            'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):

        # deletes the corresponding post
        for id in ids:
            post = Post.query.filter(Post.tempgalaxy_id == id).first()
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
        for id in ids:
            approve_tempgalaxy(id)
            flash("Galaxy has been Added")


class EditGalaxyView(ModelView):

    # edit_template = 'admin/model/temp_galaxy_edit.html'
    # list_template = 'admin/model/temp_galaxy_list.html'
    @action('approve', 'Approve')
    def action_approve(self, ids):
        for id in ids:
            approve_editgalaxy(id)
            flash("Galaxy has been Edited")

    @action('delete',
            'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):

        for id in ids:
            post = Post.query.filter(Post.editgalaxy_id == id).first()
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

    @action('approve', 'Approve')
    def action_approve(self, ids):
        for id in ids:
            approve_templine(id)

    @action('delete',
            'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):

        # deletes the corresponding post
        for id in ids:
            post = Post.query.filter(Post.templine_id == id).first()
            db.session.delete(post)
            db.session.commit()

        # deletes the corresponding temporary line
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
        for id in ids:
            approve_editline(id)

    @action('delete',
            'Delete',
            'Are you sure you want to delete selected records?')
    def action_delete(self, ids):

        for id in ids:
            post = Post.query.filter(Post.editline_id == id).first()
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


class PostsView(AdminBaseView):

    @expose('/', methods=['GET', 'POST'])
    def post_view(self):
        if request.method == "POST":
            data = request.form
            dictionary = data.to_dict(flat=True)
            for key in dictionary.keys():
                dict_of_ids = json.loads(key)
            for key, list_of_ids in dict_of_ids.items():
                if key == 'delete':
                    for id in list_of_ids:
                        id = int(id)
                        post = Post.query.filter_by(id=id).first()
                        templine_id = db.session.query(Post.templine_id).filter_by(id=id).scalar()
                        tempgalaxy_id = db.session.query(Post.tempgalaxy_id).filter_by(id=id).scalar()
                        editgalaxy_id = db.session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
                        editline_id = db.session.query(Post.editline_id).filter_by(id=id).scalar()
                        if templine_id is not None:
                            templine = TempLine.query.filter_by(id=templine_id).first()
                            db.session.delete(templine)
                        elif tempgalaxy_id is not None:
                            tempgalaxy = TempGalaxy.query.filter_by(id=tempgalaxy_id).first()
                            db.session.delete(tempgalaxy)
                        elif editgalaxy_id is not None:
                            editgalaxy = EditGalaxy.query.filter_by(id=editgalaxy_id).first()
                            db.session.delete(editgalaxy)
                        elif editline_id is not None:
                            editline = EditLine.query.filter_by(id=editline_id).first()
                            db.session.delete(editline)
                        else:
                            return "one of the posts has an id ({}) compatability issue, " \
                                   "it doesn't seem to belong to any group".format(id)
                        db.session.delete(post)
                        db.session.commit()
                elif key == 'approve':
                    for id in list_of_ids:
                        id = int(id)
                        templine_id = db.session.query(Post.templine_id).filter_by(id=id).scalar()
                        tempgalaxy_id = db.session.query(Post.tempgalaxy_id).filter_by(id=id).scalar()
                        editgalaxy_id = db.session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
                        editline_id = db.session.query(Post.editline_id).filter_by(id=id).scalar()

                        if templine_id is not None:
                            approve_templine(templine_id)

                        elif tempgalaxy_id is not None:
                            approve_tempgalaxy(tempgalaxy_id)

                        elif editgalaxy_id is not None:
                            approve_editgalaxy(editgalaxy_id)

                        elif editline_id is not None:
                            approve_editline(editline_id)

                        else:
                            return "one of the posts has an id ({}) compatability issue, " \
                                   "it doesn't seem to belong to any group".format(id)

        session = Session()
        count_of_similar_galaxies = 0
        dict_of_dict_of_similar = {}
        list_of_tempgalaxy_ids = []
        posts_of_galaxies = db.session.query(Post).filter(Post.tempgalaxy_id != None).all()
        for query in posts_of_galaxies:
            list_of_tempgalaxy_ids.append(query.tempgalaxy_id)
        for id in list_of_tempgalaxy_ids:
            id = int(id)
            tempgalaxy = db.session.query(TempGalaxy).filter_by(id=id).first()
            right_ascension = tempgalaxy.right_ascension
            declination = tempgalaxy.declination

            galaxies = db.session.query(Galaxy, Line).outerjoin(Line)

            galaxies = within_distance(galaxies, right_ascension, declination, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)

            tempgalaxies = db.session.query(TempGalaxy)
            tempgalaxies = within_distance(tempgalaxies, right_ascension, declination,
                                           based_on_beam_angle=True, temporary=True)

            similar_galaxy = galaxies.first()
            similar_tempgalaxy = tempgalaxies.first()
            dict_of_similar = {'similar_id': '', 'similar_name': '', 'similar_ra': '', 'similar_dec': '',
                               'similar_lines_approved': '', 'similar_lines_waiting_approval': '',
                               'investigated_id': '', 'investigated_name': '', 'investigated_ra': '',
                               'investigated_dec': '', 'investigated_lines_approved': '',
                               'investigated_lines_waiting_approval': '', 'relationship': ''}

            if similar_galaxy is not None:

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

                investigated_lines_waiting_approval_count = db.session.query(func.count(TempLine.id)).filter(
                    TempLine.galaxy_id == id).scalar()
                similar_lines_approved_count = db.session.query(func.count(Line.id)).filter(
                    Line.galaxy_id == int(similar_id)).scalar()
                similar_lines_waiting_approval_count = db.session.query(func.count(TempLine.id)).filter(
                    TempLine.from_existed_id == int(similar_id)).scalar()

                list_of_values = [similar_id, similar_name, similar_ra, similar_dec, similar_lines_approved_count,
                                  similar_lines_waiting_approval_count, investigated_id, investigated_name,
                                  investigated_ra, investigated_dec, investigated_lines_approved_count,
                                  investigated_lines_waiting_approval_count, 'approved_temp']
                dict_of_similar = dict(zip(dict_of_similar, list_of_values))
                dict_of_dict_of_similar[count_of_similar_galaxies] = dict_of_similar

            if (similar_tempgalaxy is not None) & (similar_tempgalaxy.id != tempgalaxy.id):

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

                investigated_lines_waiting_approval_count = session.query(func.count(TempLine.id)).filter(
                    TempLine.galaxy_id == id).scalar()
                similar_lines_waiting_approval_count = session.query(func.count(TempLine.id)).filter(
                    TempLine.galaxy_id == int(similar_id)).scalar()

                list_of_values = [similar_id, similar_name, similar_ra, similar_dec, similar_lines_approved_count,
                                  similar_lines_waiting_approval_count, investigated_id, investigated_name,
                                  investigated_ra, investigated_dec, investigated_lines_approved_count,
                                  investigated_lines_waiting_approval_count, 'temp_temp']
                dict_of_similar = dict(zip(dict_of_similar, list_of_values))
                dict_of_dict_of_similar[count_of_similar_galaxies] = dict_of_similar

        posts_query = session.query(Post, TempGalaxy, TempLine, EditGalaxy, EditLine).select_from(Post).outerjoin(
            TempGalaxy, TempGalaxy.id == Post.tempgalaxy_id).outerjoin(TempLine,
                                                                       TempLine.id == Post.templine_id).outerjoin(
            EditGalaxy, EditGalaxy.id == Post.editgalaxy_id).outerjoin(EditLine, EditLine.id == Post.editline_id).all()

        return self.render("/admin/posts.html", posts_query=posts_query,
                           dict_of_dict_of_similar=dict_of_dict_of_similar,
                           count_of_similar_galaxies=count_of_similar_galaxies)


@bp.route('/resolve/<main_id>/<other_id>/<type>/<relationship>', methods=["GET", "POST"])
@login_required
def resolve(main_id, other_id, type, relationship):
    if current_user.has_role('admin'):
        main_id = int(main_id)
        other_id = int(other_id)
        session = Session()

        if relationship == 'approved_temp':
            if type == "similar_to_investigated":

                # Approve the galaxy first
                approve_tempgalaxy(main_id)

                # Reassign temporary lines to the newly approved galaxy.
                from_existed_id = db.session.query(func.max(Galaxy.id)).first()[0]
                lines = db.session.query(Line).filter(Line.galaxy_id == other_id).all()
                for line in lines:
                    line.galaxy_id = from_existed_id

                # Delete old approved galaxy
                old_galaxy = Galaxy.query.filter_by(id=other_id).first()
                db.session.delete(old_galaxy)
                db.session.commit()

            elif type == "investigated_to_similar":

                db.session.query(TempLine).filter(TempLine.galaxy_id == other_id).update(
                    {TempLine.from_existed_id: main_id})
                db.session.commit()
                tempgalaxy = TempGalaxy.query.filter_by(id=other_id).first()
                db.session.delete(tempgalaxy)
                db.session.commit()

            elif type == "different":
                # Approve temporary first
                approve_tempgalaxy(other_id)
                # Remember similarity
                from_existed_id = session.query(func.max(Galaxy.id)).first()[0]
                galaxy_2_id = from_existed_id
                galaxy_1_id = main_id
                db.session.query(Galaxy).filter(Galaxy.id == galaxy_1_id).update({Galaxy.is_similar: galaxy_2_id})
                db.session.commit()
                db.session.query(Galaxy).filter(Galaxy.id == galaxy_2_id).update({Galaxy.is_similar: galaxy_1_id})
                db.session.commit()

        elif relationship == 'temp_temp':
            if type == "different":
                # Approve both galaxies
                # 1
                approve_tempgalaxy(other_id)

                galaxy_1_id = db.session.query(func.max(Galaxy.id)).first()[0]
                # 2
                approve_tempgalaxy(main_id)

                galaxy_2_id = db.session.query(func.max(Galaxy.id)).first()[0]

                # Remember similarity
                db.session.query(Galaxy).filter(Galaxy.id == galaxy_1_id).update({Galaxy.is_similar: galaxy_2_id})
                db.session.commit()
                db.session.query(Galaxy).filter(Galaxy.id == galaxy_2_id).update({Galaxy.is_similar: galaxy_1_id})
                db.session.commit()

            else:

                other = TempGalaxy.query.filter_by(id=other_id).first()
                post_of_other = Post.query.filter_by(tempgalaxy_id=other_id).first()

                # Approve main
                approve_tempgalaxy(main_id)

                # Reassign temporary lines to the newly approved galaxy.
                from_existed_id = db.session.query(func.max(Galaxy.id)).first()[0]
                lines = db.session.query(TempLine).filter(TempLine.galaxy_id == other_id).all()
                for line in lines:
                    line.from_existed_id = from_existed_id

                # Delete other tempgalaxy
                db.session.delete(other)
                db.session.commit()
                db.session.delete(post_of_other)
                db.session.commit()

        return redirect("/posts")

    else:
        return redirect(url_for('main.main'))


# Do we need this??? Can we not pass it as a list to /posts from the front-end?
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
    editgalaxy_id = session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
    editline_id = session.query(Post.editline_id).filter_by(id=id).scalar()
    if templine_id != None:
        templine = TempLine.query.filter_by(id=templine_id).first()
        db.session.delete(templine)
    elif tempgalaxy_id != None:
        tempgalaxy = TempGalaxy.query.filter_by(id=tempgalaxy_id).first()
        db.session.delete(tempgalaxy)
    elif editgalaxy_id != None:
        editgalaxy = EditGalaxy.query.filter_by(id=editgalaxy_id).first()
        db.session.delete(editgalaxy)
    else:
        editline = EditLine.query.filter_by(id=editline_id).first()
        db.session.delete(editline)
    db.session.delete(post)
    db.session.commit()
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
    editgalaxy_id = session.query(Post.editgalaxy_id).filter_by(id=id).scalar()
    editline_id = session.query(Post.editline_id).filter_by(id=id).scalar()

    if templine_id is not None:

        templine = TempLine.query.filter_by(id=templine_id).first()

        line = session.query(TempLine.galaxy_id, TempLine.emitted_frequency, TempLine.integrated_line_flux,
                             TempLine.integrated_line_flux_uncertainty_positive,
                             TempLine.integrated_line_flux_uncertainty_negative, TempLine.peak_line_flux,
                             TempLine.peak_line_flux_uncertainty_positive, TempLine.peak_line_flux_uncertainty_negative,
                             TempLine.line_width, TempLine.line_width_uncertainty_positive,
                             TempLine.line_width_uncertainty_negative, TempLine.observed_line_frequency,
                             TempLine.observed_line_frequency_uncertainty_positive,
                             TempLine.observed_line_frequency_uncertainty_negative, TempLine.detection_type,
                             TempLine.observed_beam_major, TempLine.observed_beam_minor, TempLine.observed_beam_angle,
                             TempLine.reference, TempLine.notes, TempLine.from_existed_id, TempLine.user_submitted,
                             TempLine.user_email, TempLine.time_submitted, TempLine.species).filter(
            TempLine.id == templine_id).first()

        if (line[20] is None):
            # line [20] represents TempLine.from_existed_id
            raise Exception('You have not yet approved the galaxy to which the line belongs to')
        else:
            g_id = line[20]
        l = Line(galaxy_id=g_id, emitted_frequency=line[1], integrated_line_flux=line[2],
                 integrated_line_flux_uncertainty_positive=line[3], integrated_line_flux_uncertainty_negative=line[4],
                 peak_line_flux=line[5], peak_line_flux_uncertainty_positive=line[6],
                 peak_line_flux_uncertainty_negative=line[7], line_width=line[8],
                 line_width_uncertainty_positive=line[9], line_width_uncertainty_negative=line[10],
                 observed_line_frequency=line[11], observed_line_frequency_uncertainty_positive=line[12],
                 observed_line_frequency_uncertainty_negative=line[13], detection_type=line[14],
                 observed_beam_major=line[15], observed_beam_minor=line[16], observed_beam_angle=line[17],
                 reference=line[18], notes=line[19], user_submitted=line[21], user_email=line[22], species=line[24])
        db.session.add(l)
        db.session.commit()
        total = update_redshift(g_id)
        update_redshift_error(g_id, total)
        db.session.delete(templine)
        db.session.commit()

    elif tempgalaxy_id is not None:

        tempgalaxy = TempGalaxy.query.filter_by(id=tempgalaxy_id).first()

        galaxy = db.session.query(TempGalaxy.name, TempGalaxy.right_ascension, TempGalaxy.declination,
                               TempGalaxy.coordinate_system, TempGalaxy.lensing_flag, TempGalaxy.classification,
                               TempGalaxy.notes).filter(TempGalaxy.id == tempgalaxy_id).first()

        g = Galaxy(name=galaxy[0], right_ascension=galaxy[1], declination=galaxy[2], coordinate_system=galaxy[3],
                   lensing_flag=galaxy[4], classification=galaxy[5], notes=galaxy[6])
        db.session.add(g)
        db.session.commit()
        existed = session.query(func.max(Galaxy.id)).first()[0]
        db.session.query(TempLine).filter(TempLine.galaxy_id == tempgalaxy_id).update(
            {TempLine.from_existed_id: existed})
        db.session.delete(tempgalaxy)
        db.session.commit()

    elif editgalaxy_id is not None:

        editgalaxy = EditGalaxy.query.filter_by(id=editgalaxy_id).first()

        galaxy = db.session.query(EditGalaxy.name, EditGalaxy.right_ascension, EditGalaxy.declination,
                                  EditGalaxy.coordinate_system, EditGalaxy.lensing_flag, EditGalaxy.classification,
                                  EditGalaxy.notes, EditGalaxy.original_id).filter(
            EditGalaxy.id == editgalaxy_id).first()
        original_id = galaxy[7]

        db.session.query(Galaxy).filter(
            Galaxy.id == original_id
        ).update(
            {"name": galaxy[0], "right_ascension": galaxy[1], "declination": galaxy[2], "coordinate_system": galaxy[3],
             "lensing_flag": galaxy[4], "classification": galaxy[5], "notes": galaxy[6]})
        db.session.delete(editgalaxy)
        db.session.commit()

    else:

        editline = EditLine.query.filter_by(id=editline_id).first()
        line = db.session.query(EditLine.galaxy_id, EditLine.original_line_id, EditLine.emitted_frequency,
                                EditLine.integrated_line_flux, EditLine.integrated_line_flux_uncertainty_positive,
                                EditLine.integrated_line_flux_uncertainty_negative, EditLine.peak_line_flux,
                                EditLine.peak_line_flux_uncertainty_positive,
                                EditLine.peak_line_flux_uncertainty_negative,
                                EditLine.line_width, EditLine.line_width_uncertainty_positive,
                                EditLine.line_width_uncertainty_negative, EditLine.observed_line_frequency,
                                EditLine.observed_line_frequency_uncertainty_positive,
                                EditLine.observed_line_frequency_uncertainty_negative, EditLine.detection_type,
                                EditLine.observed_beam_major, EditLine.observed_beam_minor,
                                EditLine.observed_beam_angle,
                                EditLine.reference, EditLine.notes, EditLine.species).filter(
            EditLine.id == editline_id).first()

        original_line_id = line[1]
        galaxy_id = line[0]

        db.session.query(Line).filter(
            Line.id == original_line_id
        ).update({"emitted_frequency": line[2], "integrated_line_flux": line[3],
                  "integrated_line_flux_uncertainty_positive": line[4],
                  "integrated_line_flux_uncertainty_negative": line[5], "peak_line_flux": line[6],
                  "peak_line_flux_uncertainty_positive": line[7], "peak_line_flux_uncertainty_negative": line[8],
                  "line_width": line[9], "line_width_uncertainty_positive": line[10],
                  "line_width_uncertainty_negative": line[11], "observed_line_frequency": line[12],
                  "observed_line_frequency_uncertainty_positive": line[13],
                  "observed_line_frequency_uncertainty_negative": line[14], "detection_type": line[15],
                  "observed_beam_major": line[16], "observed_beam_minor": line[17], "observed_beam_angle": line[18],
                  "reference": line[19], "notes": line[20], "species": line[21]})

        total = update_redshift(galaxy_id)
        update_redshift_error(galaxy_id, total)
        db.session.commit()
        # delete the edit
        db.session.delete(editline)

    db.session.delete(post)
    db.session.commit()
    return redirect("/posts")


class UserView(AdminView):
    @action('make admin',
            'Make Admin',
            'Are you sure you want to give this user admin privileges?')
    def action_make_admin(self, ids):
        for id in ids:
            user = db.session.query(User).filter(User.id == id).first()
            has_role = user_datastore.add_role_to_user(user=user, role='admin')
            db.session.add(user)
            db.session.commit()

    @action('make member',
            'Make Member',
            'Are you sure you want to delete this user\'s privileges?')
    def action_make_member(self, ids):
        for id in ids:
            user = db.session.query(User).filter(User.id == id).first()
            has_role = user_datastore.remove_role_from_user(user=user, role='admin')
            db.session.add(user)
            db.session.commit()



class FreqView(AdminBaseView):
    @expose('/', methods=['GET', 'POST'])
    def frequencies(self):
        """

        """

        form = UploadFileForm()
        if request.method == 'POST':
            csvfile = request.files['file']
            csv_file = TextIOWrapper(csvfile, encoding='utf-8-sig', errors='ignore')
            reader = csv.DictReader(x.replace('\0', '') for x in csv_file)
            data = [row for row in reader]

            for row in data:
                chemical_name = row['chemical_name'].strip()
                try:
                    species = SpeciesNames[row['species'].strip()]
                except:
                    raise SpeciesUnknownError(row['species'].strip())
                frequency = float(row['frequency'].strip())
                qn = row['qn'].strip()

                freq = Freq(chemical_name=chemical_name,
                            species=species,
                            frequency=frequency,
                            qn=qn)
                db.session.add(freq)
                db.session.commit()

        return self.render("/admin/frequencies.html", form=form)



# Commented are original model views. Can be used for troubleshooting purposes if necessary during the development.
admin.add_view(UserView(User, db.session))
# admin.add_view(AdminView(Role, db.session))
admin.add_view(AdminView(Galaxy, db.session))
admin.add_view(AdminView(Line, db.session))
admin.add_view(PostsView(name='Submissions', endpoint='posts'))
admin.add_view(AdminView(Post, db.session, category="For Developer Only"))
admin.add_view(TempGalaxyView(TempGalaxy, db.session, category="For Developer Only"))
admin.add_view(TempLineView(TempLine, db.session, category="For Developer Only"))
admin.add_view(EditGalaxyView(EditGalaxy, db.session, category="For Developer Only"))
admin.add_view(EditLineView(EditLine, db.session, category="For Developer Only"))
admin.add_view(FreqView(name='Frequencies', endpoint='frequencies', category="For Developer Only"))
admin.add_view(AdminView(Freq, db.session, category="For Developer Only"))