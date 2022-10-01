from sqlalchemy.orm import session
from app import (
    db,
    engine,
    Session
)
from flask import (
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for
)
from app.models import (
    EditGalaxy,
    EditLine,
    Galaxy,
    Line,
    Post,
    TempGalaxy,
    TempLine,
    User
)
from app.main.forms import (
    AddGalaxyForm,
    AddLineForm,
    AdvancedSearchForm,
    EditGalaxyForm,
    EditLineForm,
    EditProfileForm,
    SearchForm,
    UploadFileForm,
    DynamicSearchForm
)
from app.main.frequences import test_frequency
import csv
from sqlalchemy import func
from config import (
    COL_NAMES,
    COL_NAMES_FOR_SUBMISSION,
    ra_reg_exp,
    dec_reg_exp
)
from species import *
from io import TextIOWrapper
from flask_security import (
    current_user,
    login_required,
    roles_required
)
import math
from app.main import bp
from app.helpers import (
    to_none,
    to_zero,
    to_m_inf,
    to_p_inf,
    to_empty,
    check_decimal,
    round_to_nsf,
    round_to_uncertainty,
    round_redshift,
    ra_to_float,
    dec_to_float,
    redshift_to_frequency,
    frequency_to_redshift
)
import re
from datetime import datetime


#### HELPER FUNCTIONS ####


def within_distance(query, form_ra, form_dec, distance=0, based_on_beam_angle=False, temporary=False):
    """
    Given coordinates and distance, checks whether a galaxy exists within this distance.
    Employs Great-circle distance: https://en.wikipedia.org/wiki/Great-circle_distance .

    Parameters:
        query (db.session.query): A session object that contains all galaxies and lines that the search should consider
        form_ra (float): Right ascension of the investigated galaxy
        form_dec (float): Declination of the investigated galaxy
        distance (float): Default:0. Distance, or radius of the investigation. If based on beam angle,
        the distance is assumed to be 3 * Line.observed_beam_minor, else if Line.observed_beam_minor is not available,
        it is assumed to be 5 arcsec.
        based_on_beam_angle (bool): Default:False. Indicator whether a search should be based on the beam angle.
        temporary (bool): Default:False. Indicator whether the search should consider temporary Galaxy objects
        instead of the approved.

    Returns:
        galaxies (db.session.query): A query object containing all galaxies that satisfy the distance formula.
    """

    if not based_on_beam_angle:
        galaxies = query.filter(func.acos(
            func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(
                func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(
                func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))) < distance)
        return galaxies
    else:
        if temporary:
            galaxies = query.filter((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(
                func.radians(TempGalaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(
                func.radians(TempGalaxy.right_ascension)) * func.cos(
                func.radians(func.abs(dec_to_float(form_dec) - TempGalaxy.declination)))) < func.radians(5 / 3600)))
        else:
            subqry = db.session.query(func.max(Line.observed_beam_angle))
            sub = subqry.first()
            sub1 = sub[0]
            if sub1 is not None:
                galaxies = query.filter(((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(
                    func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(
                    func.radians(Galaxy.right_ascension)) * func.cos(
                    func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))) < (
                                              func.radians(subqry)) / 1200) & (subqry != None)) | (func.acos(
                    func.sin(func.radians(ra_to_float(form_ra))) * func.sin(
                        func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(
                        func.radians(Galaxy.right_ascension)) * func.cos(
                        func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))) < func.radians(5 / 3600)))
            else:
                galaxies = query.filter((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(
                    func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(
                    func.radians(Galaxy.right_ascension)) * func.cos(
                    func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))) < func.radians(5 / 3600)))
        return galaxies


def update_right_ascension(galaxy_id):
    """
    Updates (recalculates) average right ascension of a galaxy given right ascension of the detections.

    Parameters:
        galaxy_id (int): The id of the galaxy that will be updated.

    Returns:
        right_ascension (float | bool): The average right ascension if at least 1 line detection, False otherwise.
    """

    lines = db.session.query(Line.right_ascension).filter(Line.galaxy_id == galaxy_id).all()
    total = 0
    count = 0
    for line in lines:
        total += line[0]
        count += 1
    if count != 0:
        right_ascension = total / count
        db.session.query(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).update({"right_ascension": right_ascension})


def update_declination(galaxy_id):
    """
    Updates (recalculates) average declination of a galaxy given declination of the detections.

    Parameters:
        galaxy_id (int): The id of the galaxy that will be updated.

    Returns:
        declination (float | bool): The average declination if at least 1 line detection, False otherwise.
    """

    lines = db.session.query(Line.declination).filter(Line.galaxy_id == galaxy_id).all()
    total = 0
    count = 0
    for line in lines:
        total += line[0]
        count += 1
    if count != 0:
        declination = total / count
        db.session.query(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).update({"declination": declination})


def update_redshift(galaxy_id):
    """
    Update redshift value for a particular galaxy.

    Parameters:
        galaxy_id (int): id of the galaxy, which redshift has to be updated.

    Returns:
        sum_upper (float): Returns -1 if redshift could not be calculated, or the sum of weighted redshifts otherwise.
    """

    line_redshift = db.session.query(
        Line.emitted_frequency, Line.observed_line_redshift, Line.observed_line_redshift_uncertainty_negative,
        Line.observed_line_redshift_uncertainty_positive
    ).outerjoin(Galaxy).filter(
        Galaxy.id == galaxy_id
    ).all()

    sum_upper = sum_lower = 0
    for l in line_redshift:
        # Do not account for line entries that either do not have observed frequency value or its positive uncertainty
        if (l.observed_line_redshift_uncertainty_positive is None) or (l.observed_line_redshift is None):
            continue
        if l.observed_line_redshift == 0:
            continue
        if l.observed_line_redshift_uncertainty_negative is None:
            delta_z = 2 * l.observed_line_redshift_uncertainty_positive
        else:
            delta_z = l.observed_line_redshift_uncertainty_positive + l.observed_line_redshift_uncertainty_negative

        z = l.observed_line_redshift

        sum_upper = sum_upper + (z / delta_z)
        sum_lower = sum_lower + (1 / delta_z)
    # This case passes -1 to change redshift error, which will signal that no change needed
    if sum_lower == 0:
        return -1

    redshift_weighted = sum_upper / sum_lower
    db.session.query(Galaxy).filter(
        Galaxy.id == galaxy_id
    ).update({"redshift": redshift_weighted})
    db.session.commit()

    return sum_upper


def update_redshift_error(galaxy_id, sum_upper):
    """
    Update redshift error value for a particular galaxy.

    Parameters:
        galaxy_id (int): id of the galaxy, which redshift has to be updated.
        sum_upper (float) Sum of weighted redshifts returned by update_redshift.

    Returns:
    """

    if sum_upper != -1:

        redshift_error_weighted = 0
        line_redshift = db.session.query(
            Line.emitted_frequency, Line.observed_line_redshift, Line.observed_line_redshift_uncertainty_negative,
            Line.observed_line_redshift_uncertainty_positive
        ).outerjoin(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).all()
        for l in line_redshift:
            if (l.observed_line_redshift_uncertainty_positive is None) or (l.observed_line_redshift is None):
                continue
            if l.observed_line_redshift == 0:
                continue
            if l.observed_line_redshift_uncertainty_negative is None:
                delta_z = 2 * l.observed_line_redshift_uncertainty_positive
            else:
                delta_z = l.observed_line_redshift_uncertainty_positive + \
                           l.observed_line_redshift_uncertainty_negative

            z = l.observed_line_redshift
            weight = (z / delta_z) / sum_upper
            redshift_error_weighted = redshift_error_weighted + (weight * delta_z)
        if redshift_error_weighted != 0:
            db.session.query(Galaxy).filter(
                Galaxy.id == galaxy_id
            ).update({"redshift_error": redshift_error_weighted})
            db.session.commit()


@bp.route("/", methods=['GET'])
@bp.route("/home", methods=['GET'])
def home():
    """
    Home page route.

    On GET:
        Parameters:
            /home
            /

        Returns:
            home.html
    """

    return render_template("/home.html")


@bp.route("/contact_us", methods=['GET'])
def contact_us():
    """
    Contact us page route.

    On GET:
        Parameters:
            /contact_us

        Returns:
            contact_us.html
    """

    return render_template("/contact_us.html")


@bp.route('/user/<username>', methods=['GET'])
@login_required
def user(username):
    """
    User page. Accessible for authentificated users.

    On GET:
        Parameters:
            /user/<username> (str): Username of the corresponding user.

        Returns:
            user.html (): Populates with user's data.
    """

    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Edit user profile route. Accessible for authentificated users.

    On GET:
        Parameters:
            /edit_profile

        Returns:
            edit_profile.html (): Displays user's data.
            form (): Form prefilled with authenticated user's data.

    On POST:
        Parameters:
            /edit_profile

        Returns:
            current_user (): Commits changes on current_user's data.
            main.main (): Returns redirect to main.main.
    """

    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.university = form.university.data
        current_user.website = form.website.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been submitted")
        return redirect(url_for('main.main'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.university.data = current_user.university
        form.website.data = current_user.website
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form, user=user)


@bp.route("/main", methods=['GET', 'POST'])
def main():
    """
    Main menu route.

    On GET:
        Parameters:
            /main

        Returns:
            main.html (): Displays all database data.
            form (DynamicSearchForm): Search form.
            galaxies (db.session.query): All galaxies query.
            lines (db.session.query): All lines query.
            list_of_lines_per_species (list): List that contains counts of all lines per species per galaxy.
            count_list (list): List with integers from 0 to i, where i is the number of all galaxies.
    On POST:
        Parameters:
            /main
            form (DynamicSearchForm): Search form for galaxy by name

        Returns:
            galaxy.html (): Renders page with selected galaxy.
            galaxy (Galaxy): Searched Galaxy object.
            lines (db.session): Lines of the corresponding galaxy.
    """

    form = DynamicSearchForm()
    if form.submit.data:
        name = form.galaxy_name.data
        galaxy = Galaxy.query.filter_by(name=name).first_or_404()

        return redirect(url_for("main.galaxy", name=galaxy.name))

    galaxies = db.session.query(Galaxy).all()
    galaxies_count = db.session.query(Galaxy.id).count()

    count_list = []
    for i in range(galaxies_count):
        count_list.append(i)

    list_of_lines_per_species = []
    for i in range(galaxies_count):
        list_of_lines_per_species.append([])
        id = galaxies[i].id
        species = db.session.query(Line.species).filter(Line.galaxy_id == id).distinct()
        if species is not None:
            for s in species:
                lines_count = db.session.query(Line.id).filter((Line.galaxy_id == id) & (Line.species == s[0])).count()
                list_of_lines_per_species[i].append((s[0], lines_count))


    # rounding redshift and uncertainties.
    for galaxy in galaxies:
        galaxy.redshift, galaxy.redshift_error, _ = round_redshift(
            galaxy.redshift,
            galaxy.redshift_error,
            galaxy.redshift_error,
            True,
            False)

        species = db.session.query(Line.species).filter(Line.galaxy_id == galaxy.id).distinct()
        if species is not None:
            for s in species:
                lines_count = db.session.query(Line.id).filter((Line.galaxy_id == galaxy.id) & (Line.species == s[0])).count()
                if galaxy.lines_per_species:
                    galaxy.lines_per_species = galaxy.lines_per_species + "{}: {}\n".format(s[0], lines_count)
                else:
                    galaxy.lines_per_species = "{}: {}\n".format(s[0], lines_count)

    lines = db.session.query(Line.galaxy_id, Line.species).distinct().all()

    return render_template("/main.html", galaxies=galaxies, lines=lines,
                           list_of_lines_per_species=list_of_lines_per_species, count_list=count_list, form=form)


@bp.route('/contribute', methods=['GET'])
def contribute():
    """
    Contribution instructions page.

    On GET:
        Parameters:
            /contribute

        Returns:
            contribute.html
    """

    return render_template("contribute.html")


# Add line search given Line coordinates?
@bp.route("/query_results", methods=['GET', 'POST'])
def query_results():
    '''
    Search data route

    On access: Returns form_advanced to receive search parameters from User.
    On Search Line: Returns all line entries that fall under the given parameters
    On Search Galaxy: Returns all galaxies that (1) fall under the given parameters and (2) have at least one line entry that falls under the given parameters. 
    
    '''
    form = SearchForm()
    form_advanced = AdvancedSearchForm()
    conn = engine.connect()
    session = Session(bind=conn)

    # Post method
    if form_advanced.validate_on_submit():

        # Converts None entries to appropriate float and string entries 

        if form_advanced.name.data is None:
            form_advanced.name.data = ''
        if form_advanced.redshift_min.data is None:
            form_advanced.redshift_min.data = float('-inf')
        if form_advanced.redshift_max.data is None:
            form_advanced.redshift_max.data = float('inf')
        if form_advanced.lensing_flag.data is None or form_advanced.lensing_flag.data == 'Either':
            form_advanced.lensing_flag.data = ''
        if form_advanced.classification.data == []:
            form_advanced.classification.data = ['All']
        if form_advanced.remove_classification.data is None \
                or form_advanced.remove_classification.data == []:
            form_advanced.remove_classification.data = ''
        if form_advanced.emitted_frequency_min.data is None:
            form_advanced.emitted_frequency_min.data = float('-inf')
        if form_advanced.emitted_frequency_max.data is None:
            form_advanced.emitted_frequency_max.data = float('inf')

        if form_advanced.species.data is None or form_advanced.species.data == 'Any':
            form_advanced.species.data = ''

        if form_advanced.integrated_line_flux_min.data is None:
            form_advanced.integrated_line_flux_min.data = float('-inf')
        if form_advanced.integrated_line_flux_max.data is None:
            form_advanced.integrated_line_flux_max.data = float('inf')
        if form_advanced.peak_line_flux_min.data is None:
            form_advanced.peak_line_flux_min.data = float('-inf')
        if form_advanced.peak_line_flux_max.data is None:
            form_advanced.peak_line_flux_max.data = float('inf')
        if form_advanced.line_width_min.data is None:
            form_advanced.line_width_min.data = float('-inf')
        if form_advanced.line_width_max.data is None:
            form_advanced.line_width_max.data = float('inf')
        if form_advanced.observed_line_redshift_min.data is None:
            form_advanced.observed_line_redshift_min.data = float('-inf')
        if form_advanced.observed_line_redshift_max.data is None:
            form_advanced.observed_line_redshift_max.data = float('inf')
        if form_advanced.detection_type.data is None or form_advanced.detection_type.data == 'Either':
            form_advanced.detection_type.data = ''
        if form_advanced.observed_beam_major_min.data is None:
            form_advanced.observed_beam_major_min.data = float('-inf')
        if form_advanced.observed_beam_major_max.data is None:
            form_advanced.observed_beam_major_max.data = float('inf')
        if form_advanced.observed_beam_minor_min.data is None:
            form_advanced.observed_beam_minor_min.data = float('-inf')
        if form_advanced.observed_beam_minor_max.data is None:
            form_advanced.observed_beam_minor_max.data = float('inf')
        if form_advanced.reference.data is None:
            form_advanced.reference.data = ''

        buffer = []
        index = 0
        classification_is_all = False

        for c in form_advanced.classification.data:
            if c == "All":
                classification_is_all = True
            else:
                buffer.append(c)
                index = index + 1

        for i in range(index, 12):
            if classification_is_all:
                pass
            else:
                buffer.append("populating_list")

        # quick workaround since sqlalchemy does not take two strings equal to each other
        # otherwise a conflict in unlensed contains lensed.
        galaxy_lensing_flag_repeated = Galaxy.lensing_flag + Galaxy.lensing_flag
        form_lensing_flag_repeated = form_advanced.lensing_flag.data + form_advanced.lensing_flag.data

        # Query displaying galaxies based on the data from form_advanced
        if form_advanced.galaxySearch.data:

            # Additional filter if radius is specified
            if (form_advanced.right_ascension_point.data != None) and (
                    form_advanced.declination_point.data != None) and (
                    (form_advanced.radius_d.data != None) or (form_advanced.radius_m.data != None) or (
                    form_advanced.radius_s.data != None)):
                distance = math.radians(
                    to_zero(form_advanced.radius_d.data) + to_zero(form_advanced.radius_m.data) / 60 + to_zero(
                        form_advanced.radius_s.data) / 3600)
                galaxies = db.session.query(Galaxy, Line).outerjoin(Line)
                galaxies = within_distance(galaxies, form_advanced.right_ascension_point.data,
                                           form_advanced.declination_point.data, distance=distance)

            else:
                galaxies = db.session.query(Galaxy, Line).outerjoin(Line)

            # Filters in respect to galaxy parameters
            galaxies = galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (
                Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)),
                                               ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (
                                           Galaxy.declination.between(
                                               dec_to_float(to_m_inf(form_advanced.declination_min.data)),
                                               dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (
                                               Galaxy.redshift.between(form_advanced.redshift_min.data,
                                                                       form_advanced.redshift_max.data) | (
                                                       Galaxy.redshift == None)) & (
                                               galaxy_lensing_flag_repeated.contains(form_lensing_flag_repeated) | (Galaxy.lensing_flag == None)))
            # Check for classification
            if not classification_is_all:
                galaxies = galaxies.filter(Galaxy.classification.contains(buffer[0]) | Galaxy.classification.contains(
                    buffer[1]) | Galaxy.classification.contains(buffer[2]) | Galaxy.classification.contains(
                    buffer[3]) | Galaxy.classification.contains(buffer[4]) | Galaxy.classification.contains(
                    buffer[5]) | Galaxy.classification.contains(buffer[6]) | Galaxy.classification.contains(
                    buffer[7]) | Galaxy.classification.contains(buffer[8]) | Galaxy.classification.contains(
                    buffer[9]) | Galaxy.classification.contains(buffer[10]) | Galaxy.classification.contains(buffer[11]) | (
                                                   Galaxy.classification == None))

            galaxies = galaxies.filter(~Galaxy.classification.contains(form_advanced.remove_classification.data))

            galaxies = galaxies.filter((Line.id == None) | ((Line.emitted_frequency.between(
                form_advanced.emitted_frequency_min.data, form_advanced.emitted_frequency_max.data) | (
                                                                     Line.emitted_frequency == None)) & ((
                                                                     Line.species.contains(
                                                                         form_advanced.species.data)) | (
                                                                         Line.species == None)) & (
                                                                    Line.integrated_line_flux.between(
                                                                        form_advanced.integrated_line_flux_min.data,
                                                                        form_advanced.integrated_line_flux_max.data) | (
                                                                            Line.integrated_line_flux == None)) & (
                                                                    Line.peak_line_flux.between(
                                                                        form_advanced.peak_line_flux_min.data,
                                                                        form_advanced.peak_line_flux_max.data) | (
                                                                            Line.peak_line_flux == None)) & (
                                                                    Line.line_width.between(
                                                                        form_advanced.line_width_min.data,
                                                                        form_advanced.line_width_max.data) | (
                                                                            Line.line_width == None)) & (
                                                                    Line.observed_line_redshift.between(
                                                                        form_advanced.observed_line_redshift_min.data,
                                                                        form_advanced.observed_line_redshift_max.data) | (
                                                                            Line.observed_line_redshift == None)) & (
                                                                    Line.observed_beam_major.between(
                                                                        form_advanced.observed_beam_major_min.data,
                                                                        form_advanced.observed_beam_major_max.data) | (
                                                                            Line.observed_beam_major == None)) & (
                                                                    Line.observed_beam_minor.between(
                                                                        form_advanced.observed_beam_minor_min.data,
                                                                        form_advanced.observed_beam_minor_max.data) | (
                                                                            Line.observed_beam_minor == None)) & (
                                                                    Line.reference.contains(
                                                                        form_advanced.reference.data) | (
                                                                            Line.reference == None)) & (
                                                                    Line.detection_type.contains(
                                                                        form_advanced.detection_type.data) | (
                                                                            Line.detection_type == None))))
            # final query to be returned (if galaxy search)
            galaxies = galaxies.distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()

        # Query displaying lines based on the data from form_advanced
        elif form_advanced.lineSearch.data:
            if (form_advanced.right_ascension_point.data != None) and (
                    form_advanced.declination_point.data != None) and (
                    (form_advanced.radius_d.data != None) or (form_advanced.radius_m.data != None) or (
                    form_advanced.radius_s.data != None)):
                distance = math.radians(
                    to_zero(form_advanced.radius_d.data) + to_zero(form_advanced.radius_m.data) / 60 + to_zero(
                        form_advanced.radius_s.data) / 3600)
                galaxies = db.session.query(Galaxy, Line).outerjoin(Galaxy)
                galaxies = within_distance(galaxies, form_advanced.right_ascension_point.data,
                                           form_advanced.declination_point.data, distance=distance)

            else:
                galaxies = session.query(Galaxy, Line).outerjoin(Galaxy)

            galaxies = galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (
                Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)),
                                               ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (
                                           Galaxy.declination.between(
                                               dec_to_float(to_m_inf(form_advanced.declination_min.data)),
                                               dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (
                                               Galaxy.redshift.between(form_advanced.redshift_min.data,
                                                                       form_advanced.redshift_max.data) | (
                                                       Galaxy.redshift == None)) &
                                       (galaxy_lensing_flag_repeated.contains(form_lensing_flag_repeated) | (Galaxy.lensing_flag == None)))

            # Check for classification
            if not classification_is_all:
                galaxies = galaxies.filter(Galaxy.classification.contains(buffer[0]) | Galaxy.classification.contains(
                    buffer[1]) | Galaxy.classification.contains(buffer[2]) | Galaxy.classification.contains(
                    buffer[3]) | Galaxy.classification.contains(buffer[4]) | Galaxy.classification.contains(
                    buffer[5]) | Galaxy.classification.contains(buffer[6]) | Galaxy.classification.contains(
                    buffer[7]) | Galaxy.classification.contains(buffer[8]) | Galaxy.classification.contains(
                    buffer[9]) | Galaxy.classification.contains(buffer[10]) | Galaxy.classification.contains(
                    buffer[11]) | (Galaxy.classification == None))

            galaxies = galaxies.filter(~Galaxy.classification.contains(form_advanced.remove_classification.data))

            galaxies = galaxies.filter((Line.emitted_frequency.between(form_advanced.emitted_frequency_min.data,
                                                                       form_advanced.emitted_frequency_max.data) | (
                                                Line.emitted_frequency == None)) & (
                                               (Line.species.contains(form_advanced.species.data)) | (
                                               Line.species == None)) & (Line.integrated_line_flux.between(
                form_advanced.integrated_line_flux_min.data, form_advanced.integrated_line_flux_max.data) | (
                                                                                 Line.integrated_line_flux == None)) & (
                                               Line.peak_line_flux.between(form_advanced.peak_line_flux_min.data,
                                                                           form_advanced.peak_line_flux_max.data) | (
                                                       Line.peak_line_flux == None)) & (
                                               Line.line_width.between(form_advanced.line_width_min.data,
                                                                       form_advanced.line_width_max.data) | (
                                                       Line.line_width == None)) & (
                                               Line.observed_line_redshift.between(
                                                   form_advanced.observed_line_redshift_min.data,
                                                   form_advanced.observed_line_redshift_max.data) | (
                                                       Line.observed_line_redshift == None)) & (
                                               Line.observed_beam_major.between(
                                                   form_advanced.observed_beam_major_min.data,
                                                   form_advanced.observed_beam_major_max.data) | (
                                                       Line.observed_beam_major == None)) & (
                                               Line.observed_beam_minor.between(
                                                   form_advanced.observed_beam_minor_min.data,
                                                   form_advanced.observed_beam_minor_max.data) | (
                                                       Line.observed_beam_minor == None)) & (
                                               Line.reference.contains(form_advanced.reference.data) | (
                                               Line.reference == None)))
            # final query to be returned (if line search)
            galaxies = galaxies.order_by(Galaxy.name).all()

        # Is not called
        else:
            # final query to be returned (if general search)
            galaxies = session.query(Galaxy, Line).outerjoin(Line).distinct(Galaxy.name).group_by(Galaxy.name).order_by(
                Galaxy.name).all()

        # round values before we return query
        for object in galaxies:
            line = object[1]
            line.observed_line_redshift,\
             line.observed_line_redshift_uncertainty_positive,\
             line.observed_line_redshift_uncertainty_negative = round_redshift(
                line.observed_line_redshift,
                line.observed_line_redshift_uncertainty_positive,
                line.observed_line_redshift_uncertainty_negative
            )
        return render_template("/query_results.html", galaxies=galaxies, form=form, form_advanced=form_advanced)

    # Get method
    else:
        galaxies = session.query(Galaxy, Line).outerjoin(Line).distinct(Galaxy.name).group_by(Galaxy.name).order_by(
            Galaxy.name).all()

    return render_template("/query_results.html", form=form, form_advanced=form_advanced, galaxies=galaxies)


@bp.route("/entry_file", methods=['GET', 'POST'])
@login_required
def entry_file():
    """
    Submit CSV route. Evaluates and validates each value. If all are valid, submits for moderation, otherwise rejects
    with appropriate error message / messages.

    On GET:
        Parameters:
            /entry_file

        Returns:
            entry_file.html
            form (FlaskForm): Upload File Form.

    On Post:
        Parameters:
            'file' (.csv): Submission file

        Returns:
            db commit.
    """

    form = UploadFileForm()
    if request.method == 'POST':
        csvfile = request.files['file']
        csv_file = TextIOWrapper(csvfile, encoding='utf-8-sig', errors='ignore')
        reader = csv.DictReader(x.replace('\0', '') for x in csv_file)
        data = [row for row in reader]
        classification_options = {"LBG": "LBG (Lyman Break Galaxy)", "MS": "MS (Main Sequence Galaxy)",
                                  "SMG": "SMG (Submillimeter Galaxy)", "DSFG": "DSFG (Dusty Star-Forming Galaxy)",
                                  "SB": "SB (Starburst)", "AGN": "AGN (Contains a Known Active Galactic Nucleus)",
                                  "QSO": "QSO (Optically Bright AGN)",
                                  "Quasar": "Quasar (Optical and Radio Bright AGN)",
                                  "RQ-AGN": "RQ-AGN (Radio-Quiet AGN)", "RL-AGN": "RL-AGN (Radio-Loud AGN)",
                                  "RG": "RG (Radio Galaxy)", "BZK": "BZK (BZK-Selected Galaxy)"}

        if not data:
            flash("CSV File is empty. ")
        else:
            validated = True
            row_count = 0
            values = COL_NAMES_FOR_SUBMISSION.values()
            value_list = list(values)
            missing_column = []
            for k in value_list:
                if k not in data[0]:
                    validated = False
                    missing_column.append(k)

            if not validated:
                flash("Incorrect column names - please check sample file")
                flash("Missing Column/s : " + str(missing_column))
            for row in data:
                row_count += 1
                is_empty = True
                for element in row:
                    if row[element]:
                        is_empty = False
                if not is_empty:
                    if row == []:
                        flash("Entry " + str(row_count) + ' was an empty row')

                    # Assign and strip string values for each row
                    if validated:
                        row_name = row[COL_NAMES['name']].strip()
                        row_coordinate_system = row[COL_NAMES['coordinate_system']].strip()
                        row_lensing_flag = row[COL_NAMES['lensing_flag']].strip()
                        entered_classification = row[COL_NAMES['classification']].strip()
                        row_right_ascension = row[COL_NAMES['right_ascension']].strip()
                        row_declination = row[COL_NAMES['declination']].strip()
                        row_g_notes = row[COL_NAMES['g_notes']].strip()

                        row_emitted_frequency = row[COL_NAMES['emitted_frequency']].strip()
                        row_species = row[COL_NAMES['species']].strip()
                        row_integrated_line_flux = row[COL_NAMES['integrated_line_flux']].strip()
                        row_integrated_line_flux_uncertainty_positive = row[
                            COL_NAMES['integrated_line_flux_uncertainty_positive']].strip()
                        row_integrated_line_flux_uncertainty_negative = row[
                            COL_NAMES['integrated_line_flux_uncertainty_negative']].strip()
                        row_peak_line_flux = row[COL_NAMES['peak_line_flux']].strip()
                        row_peak_line_flux_uncertainty_positive = row[
                            COL_NAMES['peak_line_flux_uncertainty_positive']].strip()
                        row_peak_line_flux_uncertainty_negative = row[
                            COL_NAMES['peak_line_flux_uncertainty_negative']].strip()
                        row_line_width = row[COL_NAMES['line_width']].strip()
                        row_line_width_uncertainty_positive = row[COL_NAMES['line_width_uncertainty_positive']].strip()
                        row_line_width_uncertainty_negative = row[COL_NAMES['line_width_uncertainty_negative']].strip()
                        row_freq_type = row[COL_NAMES['freq_type']].strip()
                        row_observed_line_redshift = row[COL_NAMES['observed_line_redshift']].strip()
                        row_observed_line_redshift_uncertainty_positive = row[
                            COL_NAMES['observed_line_redshift_uncertainty_positive']].strip()
                        row_observed_line_redshift_uncertainty_negative = row[
                            COL_NAMES['observed_line_redshift_uncertainty_negative']].strip()
                        row_detection_type = row[COL_NAMES['detection_type']].strip()
                        row_observed_beam_major = row[COL_NAMES['observed_beam_major']].strip()
                        row_observed_beam_minor = row[COL_NAMES['observed_beam_minor']].strip()
                        row_observed_beam_angle = row[COL_NAMES['observed_beam_angle']].strip()
                        row_reference = row[COL_NAMES['reference']].strip()
                        row_notes = row[COL_NAMES['l_notes']].strip()

                        # Check whether the values pass the conditions
                        if row_name == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Galaxy Name is Mandatory")
                        if row_coordinate_system != "ICRS" and row_coordinate_system != "J2000":
                            validated = False
                            flash("Entry " + str(row_count) + ": Coordinate System can be ICRS or J2000 only.")
                        if row_lensing_flag != "Lensed" and row_lensing_flag != "Unlensed" and row_lensing_flag != "":
                            if row_lensing_flag != "L" and row_lensing_flag != "U" and row_lensing_flag != "l" and row_lensing_flag != "u":
                                validated = False
                                flash("Entry " + str(
                                    row_count) + ": Please enter either \"Lensed\", \"Unlensed\" or \"L\", \"U\" under {}.".format(
                                    row_lensing_flag))

                        if entered_classification == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Classification is Mandatory")
                        row_classification = ""
                        for key, value in classification_options.items():
                            if key in entered_classification.upper():
                                row_classification = row_classification + "," + key
                        if row_classification == "," or row_classification == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Please enter Correction Classifications")
                        if row_right_ascension == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Right Ascension is Mandatory")
                        if re.search(ra_reg_exp, row_right_ascension) == None:
                            validated = False
                            flash("Entry " + str(row_count) + ": Enter Right Ascension in a proper format")
                        if row_declination == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Declination is Mandatory")
                        if re.search(dec_reg_exp, row_declination) == None:
                            validated = False
                            flash("Entry " + str(row_count) + ": Enter Declination in a proper format")
                        if row_emitted_frequency == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Emitted Frequency is Mandatory")

                        try:
                            dict_frequency, message = test_frequency(row_species, row_emitted_frequency)
                            if not dict_frequency:
                                flash("Entry " + str(row_count) + message)
                                validated = False
                        except:
                            pass
                        if row_species == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Please specify species")
                        if row_integrated_line_flux == "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Integrated Line Flux is Mandatory")
                        if row_integrated_line_flux_uncertainty_positive == "":
                            validated = False
                            flash(
                                "Entry " + str(row_count) + ": Integrated Line Flux Positive Uncertainty is Mandatory")
                        if row_integrated_line_flux_uncertainty_negative == "":
                            validated = False
                            flash(
                                "Entry " + str(row_count) + ": Integrated Line Flux Negative Uncertainty is Mandatory")
                        if row_integrated_line_flux_uncertainty_positive != "":
                            try:
                                if float(row_integrated_line_flux_uncertainty_positive) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Integrated Line Flux Positive Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_integrated_line_flux_uncertainty_negative != "":
                            try:
                                if float(row_integrated_line_flux_uncertainty_negative) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Integrated Line Flux Negative Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_peak_line_flux_uncertainty_positive != "":
                            try:
                                if float(row_peak_line_flux_uncertainty_positive) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Peak Line Flux Positive Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_peak_line_flux_uncertainty_negative != "":
                            try:
                                if float(row_peak_line_flux_uncertainty_negative) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Peak Line Flux Negative Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_line_width_uncertainty_positive != "":
                            try:
                                if float(row_line_width_uncertainty_positive) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Line Width Positive Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_line_width_uncertainty_negative != "":
                            try:
                                if float(row_line_width_uncertainty_negative) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Line Width Negative Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_freq_type != "z" and row_freq_type != "f" and row_freq_type != "":
                            validated = False
                            flash("Entry " + str(row_count) + ": Please enter either \"z\", \"f\" under {}.".format(
                                row_freq_type))
                        if row_observed_line_redshift_uncertainty_positive != "":
                            try:
                                if float(row_observed_line_redshift_uncertainty_positive) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Observed Line Frequency Positive Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_observed_line_redshift_uncertainty_negative != "":
                            try:
                                if float(row_observed_line_redshift_uncertainty_negative) < 0:
                                    validated = False
                                    flash("Entry " + str(
                                        row_count) + ": Observed Line Frequency Negative Uncertainty must be greater than 0")
                            except:
                                pass

        # If passed all conditions
        if validated:
            flash("All entered values are valid")
            for row in data:

                # Assign and strip string values for each row
                row_name = row[COL_NAMES['name']].strip()
                row_coordinate_system = row[COL_NAMES['coordinate_system']].strip()
                row_lensing_flag = row[COL_NAMES['lensing_flag']].strip()
                row_right_ascension = row[COL_NAMES['right_ascension']].strip()
                row_declination = row[COL_NAMES['declination']].strip()
                row_g_notes = row[COL_NAMES['g_notes']].strip()
                entered_classification = row[COL_NAMES['classification']].strip()
                row_classification = ""
                for key, value in classification_options.items():
                    if key in entered_classification:
                        row_classification = row_classification + ", " + key
                row_classification = row_classification[2:]
                row_emitted_frequency = row[COL_NAMES['emitted_frequency']].strip()
                row_species = row[COL_NAMES['species']].strip()
                row_integrated_line_flux = row[COL_NAMES['integrated_line_flux']].strip()
                row_integrated_line_flux_uncertainty_positive = row[
                    COL_NAMES['integrated_line_flux_uncertainty_positive']].strip()
                row_integrated_line_flux_uncertainty_negative = row[
                    COL_NAMES['integrated_line_flux_uncertainty_negative']].strip()
                if row_integrated_line_flux_uncertainty_negative == "":
                    row_integrated_line_flux_uncertainty_negative = row_integrated_line_flux_uncertainty_positive
                row_peak_line_flux = row[COL_NAMES['peak_line_flux']].strip()
                row_peak_line_flux_uncertainty_positive = row[COL_NAMES['peak_line_flux_uncertainty_positive']].strip()
                row_peak_line_flux_uncertainty_negative = row[COL_NAMES['peak_line_flux_uncertainty_negative']].strip()
                if row_peak_line_flux_uncertainty_negative == "":
                    row_peak_line_flux_uncertainty_negative = row_peak_line_flux_uncertainty_positive
                row_line_width = row[COL_NAMES['line_width']].strip()
                row_line_width_uncertainty_positive = row[COL_NAMES['line_width_uncertainty_positive']].strip()
                row_line_width_uncertainty_negative = row[COL_NAMES['line_width_uncertainty_negative']].strip()
                if row_line_width_uncertainty_negative == "":
                    row_line_width_uncertainty_negative = row_line_width_uncertainty_positive
                row_freq_type = row[COL_NAMES['freq_type']].strip()
                row_observed_line_redshift = row[COL_NAMES['observed_line_redshift']].strip()
                row_observed_line_redshift_uncertainty_positive = row[
                    COL_NAMES['observed_line_redshift_uncertainty_positive']].strip()
                row_observed_line_redshift_uncertainty_negative = row[
                    COL_NAMES['observed_line_redshift_uncertainty_negative']].strip()
                if row_observed_line_redshift_uncertainty_negative == "":
                    row_observed_line_redshift_uncertainty_negative = row_observed_line_redshift_uncertainty_positive
                row_detection_type = row[COL_NAMES['detection_type']].strip()
                row_observed_beam_major = row[COL_NAMES['observed_beam_major']].strip()
                row_observed_beam_minor = row[COL_NAMES['observed_beam_minor']].strip()
                row_observed_beam_angle = row[COL_NAMES['observed_beam_angle']].strip()
                row_reference = row[COL_NAMES['reference']].strip()
                row_notes = row[COL_NAMES['l_notes']].strip()

                ra = ra_to_float(row_right_ascension)
                dec = dec_to_float(row_declination)

                # Make lensing flag in standard notation:
                if row_lensing_flag != "Lensed" and row_lensing_flag != "Unlensed" and row_lensing_flag != "":
                    if row_lensing_flag == "U" or row_lensing_flag == "u":
                        row_lensing_flag = "Unlensed"
                    else:
                        row_lensing_flag = "Lensed"

                # Check whether this galaxy entry has been previously uploaded and/or approved
                galaxies = db.session.query(Galaxy, Line).outerjoin(Line).filter(Galaxy.name == row_name)
                galaxies = within_distance(galaxies, ra, dec, based_on_beam_angle=True)
                galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)

                tempgalaxies = db.session.query(TempGalaxy).filter(TempGalaxy.name == row_name)
                tempgalaxies = within_distance(tempgalaxies, ra, dec, based_on_beam_angle=True, temporary=True)

                similar_galaxy = galaxies.first()
                similar_tempgalaxy = tempgalaxies.first()

                # If this galaxy entry has not been previously uploaded and/or approved, then upload.
                if (similar_tempgalaxy is None) & (similar_galaxy is None):

                    galaxy = TempGalaxy(name=row_name,
                                        right_ascension=ra,
                                        declination=dec,
                                        coordinate_system=row_coordinate_system,
                                        lensing_flag=row_lensing_flag,
                                        classification=row_classification,
                                        notes=row_g_notes,
                                        user_submitted=current_user.username,
                                        user_email=current_user.email,
                                        time_submitted=datetime.utcnow())
                    db.session.add(galaxy)

                    from_existed = None
                    tempgalaxy_id = db.session.query(func.max(TempGalaxy.id)).first()[0]
                    post = Post(tempgalaxy_id=tempgalaxy_id, user_email=current_user.email,
                                time_submitted=datetime.utcnow())
                    # We use the id variable in line submission below.
                    id = tempgalaxy_id
                    db.session.add(post)
                    db.session.commit()
                # If this galaxy has been previously uploaded but not yet approved / deleted,
                # then remember id to assign the corresponding line submission.
                elif (similar_tempgalaxy is not None) & (similar_galaxy is None):
                    id = similar_tempgalaxy.id
                    from_existed = None
                # If this galaxy has been previously approved and is stored in db,
                # then remember id to assign the corresponding line submissions.
                else:
                    id = similar_galaxy[0].id
                    from_existed = id

                dict_frequency, message = test_frequency(row_species, row_emitted_frequency)

                # Since v-1.12 we convert observed frequency to redshift and store as redshift.

                if row_freq_type == "f":
                    frequency, positive_uncertainty, negative_uncertainty = frequency_to_redshift(dict_frequency,
                                                                            to_none(row_observed_line_redshift),
                                                                            to_none(row_observed_line_redshift_uncertainty_positive),
                                                                            to_none(
                                                                               row_observed_line_redshift_uncertainty_negative))

                else:
                    frequency = to_none(row_observed_line_redshift)
                    positive_uncertainty = to_none(row_observed_line_redshift_uncertainty_positive)
                    negative_uncertainty = to_none(row_observed_line_redshift_uncertainty_negative)

                # Check whether this line entry has been previously uploaded and/or approved
                check_same_temp_line = db.session.query(TempLine.id).filter(
                    (TempLine.emitted_frequency == dict_frequency) & (TempLine.observed_line_redshift == frequency) & (
                            TempLine.galaxy_name == row_name) & (TempLine.species == row_species) & (
                            TempLine.integrated_line_flux == to_none(row_integrated_line_flux)) & (
                            TempLine.integrated_line_flux_uncertainty_positive == to_none(
                            row_integrated_line_flux_uncertainty_positive))).first()

                galaxy_id = db.session.query(Galaxy.id).filter_by(name=row_name).scalar()

                check_same_line = db.session.query(Line.id).filter(
                    (Line.galaxy_id == galaxy_id) & (Line.emitted_frequency == dict_frequency) & (
                            Line.observed_line_redshift == frequency) & (
                            Line.integrated_line_flux == to_none(row_integrated_line_flux)) & (
                            Line.integrated_line_flux_uncertainty_positive == to_none(
                            row_integrated_line_flux_uncertainty_positive)) & (Line.species == row_species)).first()

                # If this galaxy entry has not been previously uploaded and/or approved, then upload. 
                if (check_same_temp_line is None) & (check_same_line is None):

                    line = TempLine(galaxy_id=id,
                                    from_existed_id=from_existed,
                                    emitted_frequency=dict_frequency,
                                    species=row_species,
                                    integrated_line_flux=to_none(row_integrated_line_flux),
                                    integrated_line_flux_uncertainty_positive=to_none(
                                        row_integrated_line_flux_uncertainty_positive),
                                    integrated_line_flux_uncertainty_negative=to_none(
                                        row_integrated_line_flux_uncertainty_negative),
                                    peak_line_flux=to_none(row_peak_line_flux),
                                    peak_line_flux_uncertainty_positive=to_none(
                                        row_peak_line_flux_uncertainty_positive),
                                    peak_line_flux_uncertainty_negative=to_none(
                                        row_peak_line_flux_uncertainty_negative),
                                    line_width=to_none(row_line_width),
                                    line_width_uncertainty_positive=to_none(row_line_width_uncertainty_positive),
                                    line_width_uncertainty_negative=to_none(row_line_width_uncertainty_negative),
                                    observed_line_redshift=frequency,
                                    observed_line_redshift_uncertainty_positive=positive_uncertainty,
                                    observed_line_redshift_uncertainty_negative=negative_uncertainty,
                                    detection_type=row_detection_type,
                                    observed_beam_major=to_none(row_observed_beam_major),
                                    observed_beam_minor=to_none(row_observed_beam_minor),
                                    observed_beam_angle=to_none(row_observed_beam_angle),
                                    reference=row_reference,
                                    notes=row_notes,
                                    user_submitted=current_user.username,
                                    user_email=current_user.email,
                                    time_submitted=datetime.utcnow(),
                                    galaxy_name=row_name,
                                    right_ascension=ra,
                                    declination=dec
                                    )
                    db.session.add(line)

                    try:
                        db.session.commit()
                        templine = db.session.query(func.max(TempLine.id)).first()
                        templine_id = int(templine[0])
                        post = Post(templine_id=templine_id, user_email=current_user.email,
                                    time_submitted=datetime.utcnow())
                        db.session.add(post)
                        db.session.commit()
                        # flash ("Entry number {} has been successfully uploaded.".format(row_count))
                    except:
                        db.session.rollback()

                else:
                    # If this line entry already exists in db, pass.
                    pass

            flash('Entries have been successfully uploaded and await moderator approval.')
        else:
            flash('File not uploaded. Please resubmit the file once corrected.')

    return render_template("/entry_file.html", title="Upload File", form=form)


@bp.route("/galaxy_entry_form", methods=['GET', 'POST'])
@login_required
def galaxy_entry_form():
    """
    Galaxy entry form route. If the entry seems to exist already in the database or if its coordinates
    closely resemble the coordinates of an existing galaxy, then a clarification is returned
    with the list of the galaxies that the User could potentially mean. Otherwise, the entry is uploaded.

    On GET:
        Parameters:
            /galaxy_entry_form

        Returns:
            form (FlaskForm): AddGalaxyForm
            galaxy_entry_form.html

    On POST:
        Parameters:
            form (FlaskForm): Filled form with data to be committed.

        Returns:
            db commit.
    """

    form = AddGalaxyForm()
    session = Session()
    if form.validate_on_submit():

        if form.submit.data:

            dec = dec_to_float(form.declination.data)
            ra = ra_to_float(form.right_ascension.data)

            # Check whether this galaxy entry has been previously uploaded and/or approved
            galaxies = db.session.query(Galaxy, Line).outerjoin(Line)
            galaxies = within_distance(galaxies, ra, dec, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)

            tempgalaxies = session.query(TempGalaxy)
            tempgalaxies = within_distance(tempgalaxies, ra, dec, based_on_beam_angle=True, temporary=True)

            similar_galaxy = galaxies.first()
            similar_tempgalaxy = tempgalaxies.first()

            # If was previously submitted / approved, redirect the user to the confirmation post whether they still
            # want to submit.
            if (similar_galaxy is not None) or (similar_tempgalaxy is not None):
                if similar_galaxy is not None:
                    another_exists = True
                else:
                    another_exists = False
                if similar_tempgalaxy is not None:
                    same_temp_exists = True
                else:
                    same_temp_exists = False
                return render_template('galaxy_entry_form.html', title='Galaxy Entry Form', form=form,
                                       galaxies=galaxies, same_temp_exists=same_temp_exists,
                                       another_exists=another_exists)

            # Otherwise, if the galaxy was not found in db, submit.
            # Parse the list with full classification names into a simple string like "QSO,AGN"
            classifications = ''.join([re.sub(r' [(][^)]*[)]', '', elem) + "," for elem in form.classification.data])[:-1]
            galaxy = TempGalaxy(name=form.name.data, right_ascension=ra, declination=dec,
                                coordinate_system=form.coordinate_system.data, classification=classifications,
                                lensing_flag=form.lensing_flag.data, notes=form.notes.data,
                                user_submitted=current_user.username, user_email=current_user.email, is_similar=None,
                                time_submitted=datetime.utcnow())
            db.session.add(galaxy)
            db.session.commit()
            tempgalaxy_id = db.session.query(func.max(TempGalaxy.id)).first()[0]
            post = Post(tempgalaxy_id=tempgalaxy_id, user_email=current_user.email, time_submitted=datetime.utcnow())
            db.session.add(post)
            db.session.commit()
            flash('Galaxy has been added. ')

        # If User still wants to submit the entry even though similar exist.
        if form.submit_anyway.data:
            dec = dec_to_float(form.declination.data)
            ra = ra_to_float(form.right_ascension.data)

            classifications = ''.join([re.sub(r' [(][^)]*[)]', '', elem) + "," for elem in form.classification.data])[:-1]
            galaxy = TempGalaxy(name=form.name.data, right_ascension=ra, declination=dec,
                                coordinate_system=form.coordinate_system.data, classification=classifications,
                                lensing_flag=form.lensing_flag.data, notes=form.notes.data,
                                user_submitted=current_user.username, user_email=current_user.email, is_similar=None,
                                time_submitted=datetime.utcnow())
            db.session.add(galaxy)
            db.session.commit()
            tempgalaxy_id = db.session.query(func.max(TempGalaxy.id)).first()[0]
            post = Post(tempgalaxy_id=tempgalaxy_id, user_email=current_user.email, time_submitted=datetime.utcnow())
            db.session.add(post)
            db.session.commit()
            flash('Galaxy has been added. ')

        # If User preferred not to submit the entry. 
        if form.do_not_submit.data:
            return redirect(url_for('main.main'))

        # If User wants to add a line entry to just submitted galaxy entry. 
        if form.new_line.data:
            return redirect(url_for('main.line_entry_form'))
    return render_template('galaxy_entry_form.html', title='Galaxy Entry Form', form=form)


@bp.route("/galaxy_edit_form/<id>", methods=['GET', 'POST'])
@login_required
def galaxy_edit_form(id):
    """
    Galaxy edit route
    On access: Prefills the form with the desired galaxy to be edited.
    On submit: Submits the edits. An error is raised if unappropriated values are entered.
    On GET:
        Parameters:
            /galaxy_edit_form
            id (str): The id of the galaxy under edit.

        Returns:
            form (FlaskForm): EditGalaxyForm
            galaxy_entry_form.html

    On POST:
        Parameters:
            /galaxy_edit_form
        Returns:
            db commit.
    """

    galaxy = db.session.query(Galaxy).filter(Galaxy.id == id).first()
    classifications = galaxy.classification
    classification_list = galaxy.classification.split(',')

    form = EditGalaxyForm(name=galaxy.name, coordinate_system=galaxy.coordinate_system,
                          lensing_flag=galaxy.lensing_flag, classification=classifications, notes=galaxy.notes)
    form.classification.data = classifications
    original_id = galaxy.id

    if form.validate_on_submit():
        if form.submit.data:
            changes = ""
            removeclass = form.remove_classification.data
            addclass = form.add_classification.data
            for element in removeclass:
                if element in classification_list:
                    classification_list.remove(element)
                else:
                    flash(element + " was not in the existing list")
            for element in addclass:
                if element not in classification_list:
                    classification_list.append(element)
                else:
                    flash(element + " already exists")
            newclasslist = ''.join([str(elem) + "," for elem in classification_list])[:-1]
            if galaxy.name != form.name.data:
                changes = changes + 'Initial Name: ' + galaxy.name + ' New Name: ' + form.name.data
            if galaxy.coordinate_system != form.coordinate_system.data:
                changes = changes + 'Initial Coordinate System: ' + galaxy.coordinate_system \
                          + ' New Coordinate System: ' + form.coordinate_system.data
            if galaxy.lensing_flag != form.lensing_flag.data:
                changes = changes + 'Initial Lensing Flag: ' + galaxy.lensing_flag \
                          + ' New Lensing Flag: ' + form.lensing_flag.data
            if galaxy.classification != newclasslist:
                changes = changes + 'Initial Classification: ' + galaxy.classification \
                          + ' New Classification: ' + newclasslist
            if galaxy.notes != form.notes.data:
                try:
                    changes = changes + 'Initial Notes: ' + galaxy.notes + 'New Notes: ' + form.notes.data
                except:
                    if galaxy.notes == None:
                        changes = changes + 'Initial Notes: ' + "None " + 'New Notes: ' + form.notes.data
                    elif form.notes.data == None:
                        changes = changes + 'Initial Notes: ' + galaxy.notes + 'New Notes: ' + "None"

            editgalaxy = EditGalaxy(name=form.name.data, right_ascension=galaxy.right_ascension,
                                declination=galaxy.declination, coordinate_system=form.coordinate_system.data,
                                classification=newclasslist, lensing_flag=form.lensing_flag.data, notes=form.notes.data,
                                user_submitted=current_user.username, user_email=current_user.email, is_edited=changes,
                                original_id=original_id)
            db.session.add(editgalaxy)
            db.session.commit()

            # Adding the corresponding post
            editgalaxy_id = int(db.session.query(func.max(EditGalaxy.id)).first()[0])
            post = Post(editgalaxy_id=editgalaxy_id, user_email=current_user.email, time_submitted=datetime.utcnow())
            db.session.add(post)
            db.session.commit()

            flash('Galaxy has been Edited. ')
        if form.new_line.data:
            return redirect(url_for('main.line_entry_form'))
    return render_template('galaxy_edit_form.html', title='Galaxy Edit Form', form=form)


@bp.route("/line_entry_form", methods=['GET', 'POST'])
@login_required
def line_entry_form():
    """
    Line entry route

    On GET:
        Parameters:
            /line_entry_form

        Returns:
            form (FlaskForm): AddLineForm
            line_entry_form.html

    On POST:
        Parameters:
            /galaxy_edit_form
        Returns:
            db commit.
            redirect to main.main.
    """

    name = ""
    form = AddLineForm()
    if form.galaxy_form.data:
        return redirect(url_for('main.galaxy_entry_form'))
    if form.validate_on_submit():
        if form.submit.data:
            # Attempt to find the desired galaxy by name among the approved.
            galaxy_id = db.session.query(Galaxy.id).filter(Galaxy.name == form.galaxy_name.data).scalar()
            try:
                id = galaxy_id
                name = db.session.query(Galaxy.name).filter(Galaxy.id == id).scalar()
            except:
                id = None
            existed = id
            tempgalaxy_id = None
            # If the galaxy was not found among the approved, find among the not yet approved.
            if galaxy_id is None:
                galaxy_id = db.session.query(TempGalaxy.id).filter(TempGalaxy.name == form.galaxy_name.data).scalar()
                id = galaxy_id
                name = db.session.query(TempGalaxy.name).filter(TempGalaxy.id == id).scalar()
                tempgalaxy_id = id
                existed = None
            # If the galaxy was still not found, we assume the name was misspelled and we flash a message,
            # otherwise we proceed with the submission.
            if galaxy_id is None:
                flash('Please enter the name exactly as proposed using Caps if necessary')
            else:
                try:
                    dict_frequency, message = test_frequency(form.species.data, form.emitted_frequency.data)
                    if not dict_frequency:
                        flash(message)
                except:
                    #define exception here
                    pass

                dict_frequency, message = test_frequency(form.species.data, form.emitted_frequency.data)

                if form.freq_type.data == 'f':
                    frequency, positive_uncertainty, negative_uncertainty = frequency_to_redshift(dict_frequency,
                                                                            form.observed_line_redshift.data,
                                                                            form.observed_line_redshift_uncertainty_positive.data,
                                                                            form.observed_line_redshift_uncertainty_negative.data)
                else:
                    frequency = form.observed_line_redshift.data
                    positive_uncertainty = form.observed_line_redshift_uncertainty_positive.data
                    negative_uncertainty = form.observed_line_redshift_uncertainty_negative.data

                # Check whether this line entry has been previously uploaded and/or approved
                check_same_temp_line = db.session.query(TempLine.id).filter(
                    (TempLine.emitted_frequency == dict_frequency) & (TempLine.observed_line_redshift == frequency) & (
                            TempLine.galaxy_name == form.galaxy_name.data) & (
                            TempLine.species == form.species.data) & (
                            TempLine.integrated_line_flux == to_none(form.integrated_line_flux.data)) & (
                            TempLine.integrated_line_flux_uncertainty_positive == to_none(
                        form.integrated_line_flux_uncertainty_positive.data))).first()

                check_same_line = db.session.query(Line.id).filter(
                    (Line.galaxy_id == galaxy_id) & (Line.emitted_frequency == dict_frequency) & (
                            Line.observed_line_redshift == frequency) & (
                            Line.integrated_line_flux == to_none(form.integrated_line_flux.data)) & (
                            Line.integrated_line_flux_uncertainty_positive == to_none(
                        form.integrated_line_flux_uncertainty_positive.data)) & (
                            Line.species == form.species.data)).first()

                # If this galaxy entry has not been previously uploaded and/or approved, then upload. 
                if (check_same_line is None) & (check_same_temp_line is None):
                    line = TempLine(galaxy_id=id,
                                    emitted_frequency=form.emitted_frequency.data,
                                    species=form.species.data,
                                    integrated_line_flux=form.integrated_line_flux.data,
                                    integrated_line_flux_uncertainty_positive=form.integrated_line_flux_uncertainty_positive.data,
                                    integrated_line_flux_uncertainty_negative=form.integrated_line_flux_uncertainty_negative.data,
                                    peak_line_flux=form.peak_line_flux.data,
                                    peak_line_flux_uncertainty_positive=form.peak_line_flux_uncertainty_positive.data,
                                    peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data,
                                    line_width=form.line_width.data,
                                    line_width_uncertainty_positive=form.line_width_uncertainty_positive.data,
                                    line_width_uncertainty_negative=form.line_width_uncertainty_negative.data,
                                    observed_line_redshift=frequency,
                                    observed_line_redshift_uncertainty_positive=positive_uncertainty,
                                    observed_line_redshift_uncertainty_negative=negative_uncertainty,
                                    detection_type=form.detection_type.data,
                                    observed_beam_major=form.observed_beam_major.data,
                                    observed_beam_minor=form.observed_beam_minor.data,
                                    observed_beam_angle=form.observed_beam_angle.data,
                                    reference=form.reference.data,
                                    notes=form.notes.data,
                                    user_submitted=current_user.username,
                                    user_email=current_user.email,
                                    from_existed_id=existed,
                                    galaxy_name=name,
                                    right_ascension=ra_to_float(form.right_ascension.data),
                                    declination=dec_to_float(form.declination.data))
                    db.session.add(line)
                    db.session.commit()
                    templine_id = db.session.query(func.max(TempLine.id)).first()[0]
                    post = Post(templine_id=templine_id,
                                tempgalaxy_id=tempgalaxy_id,
                                user_email=current_user.email,
                                time_submitted=datetime.utcnow()
                                )
                    db.session.add(post)
                    db.session.commit()
                else:
                    pass
                flash('Line has been added. ')
                return redirect(url_for('main.main'))
    return render_template('line_entry_form.html', title='Line Entry Form', form=form)


@bp.route("/line_edit_form/<id>", methods=['GET', 'POST'])
@login_required
def line_edit_form(id):
    """
    Line edit route

    On GET:
        Parameters:
            /line_edit_form
            id (str): The id of the line under edit.

        Returns:
            form (FlaskForm): EditLineForm

    On POST:
        Parameters:
            /line_edit_form
        Returns:
            db commit.
    """

    line = db.session.query(Line).filter(Line.id == id).first()

    name = db.session.query(Galaxy.name).filter(Galaxy.id == line.galaxy_id).scalar()
    form = EditLineForm(galaxy_name=name, emitted_frequency=line.emitted_frequency, species=line.species,
                        integrated_line_flux=line.integrated_line_flux,
                        integrated_line_flux_uncertainty_positive=line.integrated_line_flux_uncertainty_positive,
                        peak_line_flux=line.peak_line_flux,
                        peak_line_flux_uncertainty_positive=line.peak_line_flux_uncertainty_positive,
                        line_width=line.line_width,
                        line_width_uncertainty_positive=line.line_width_uncertainty_positive,
                        observed_line_redshift=line.observed_line_redshift,
                        observed_line_redshift_uncertainty_positive=line.observed_line_redshift_uncertainty_positive,
                        detection_type=line.detection_type, observed_beam_major=line.observed_beam_major,
                        observed_beam_minor=line.observed_beam_minor, observed_beam_angle=line.observed_beam_angle,
                        reference=line.reference, notes=line.notes)
    if form.galaxy_form.data:
        return redirect(url_for('main.galaxy_entry_form'))
    if form.validate_on_submit():
        if form.submit.data:
            galaxy_id = db.session.query(Galaxy.id).filter(Galaxy.name == form.galaxy_name.data).scalar()

            if galaxy_id is None:
                flash('Please enter the name exactly as proposed using Caps if necessary')
            else:
                dict_frequency, message = test_frequency(str(form.species.data), str(form.emitted_frequency.data))
                if not dict_frequency:
                    flash(message)
                if form.freq_type.data == 'f':
                    frequency, positive_uncertainty, negative_uncertainty = frequency_to_redshift(dict_frequency,
                                                                            form.observed_line_redshift.data,
                                                                            form.observed_line_redshift_uncertainty_positive.data,
                                                                            form.observed_line_redshift_uncertainty_negative.data)
                else:
                    frequency = form.observed_line_redshift.data
                    positive_uncertainty = form.observed_line_redshift_uncertainty_positive.data
                    negative_uncertainty = form.observed_line_redshift_uncertainty_negative.data

                changes = ""
                if line.emitted_frequency != float(form.emitted_frequency.data):
                    changes = changes + "Initial Emitted Frequency: " + str(
                        line.emitted_frequency) + " New Emitted Frequency: " + str(form.emitted_frequency.data)
                if line.species != form.species.data:
                    changes = changes + "Initial Species: " + str(line.species) + " New Species: " + str(form.species.data)
                if line.integrated_line_flux != float(form.integrated_line_flux.data):
                    changes = changes + "Initial Integrated Line Flux: " + str(line.integrated_line_flux) +\
                              " New Integrated Line Flux: " + str(form.integrated_line_flux.data)
                if form.integrated_line_flux_uncertainty_positive.data:
                    if float(line.integrated_line_flux_uncertainty_positive) != float(
                            form.integrated_line_flux_uncertainty_positive.data):
                        changes = changes + "Initial Integrated Line Flux Positive Uncertainty: " +\
                                  str(line.integrated_line_flux_uncertainty_positive) +\
                                  " New Integrated Line Flux Positive Uncertainty: " +\
                                  str(form.integrated_line_flux_uncertainty_positive.data)
                if form.integrated_line_flux_uncertainty_negative.data:
                    if float(line.integrated_line_flux_uncertainty_negative) != float(
                            form.integrated_line_flux_uncertainty_negative.data):
                        changes = changes + "Initial Integrated Line Flux Negative Uncertainty: " +\
                                  str(line.integrated_line_flux_uncertainty_negative) +\
                                  " New Integrated Line Flux Negative Uncertainty: " +\
                                  str(form.integrated_line_flux_uncertainty_negative.data)
                if form.peak_line_flux.data:
                    if float(line.peak_line_flux) != float(form.peak_line_flux.data):
                        changes = changes + "Initial Peak Line Flux: " +\
                                  str(line.peak_line_flux) + " New Peak Line Flux: " +\
                                  str(form.peak_line_flux.data)
                if form.peak_line_flux_uncertainty_positive.data:
                    if float(line.peak_line_flux_uncertainty_positive) != float(
                            form.peak_line_flux_uncertainty_positive.data):
                        changes = changes + "Initial Peak Line Flux Positive Uncertainty: " +\
                                  str(line.peak_line_flux_uncertainty_positive) +\
                                  " New Peak Line Flux Positive Uncertainty: "\
                                  + str(form.peak_line_flux_uncertainty_positive.data)
                if form.peak_line_flux_uncertainty_negative.data:
                    if float(line.peak_line_flux_uncertainty_negative) != float(
                            form.peak_line_flux_uncertainty_negative.data):
                        changes = changes + "Initial Peak Line Flux Negative Uncertainty: " +\
                                  str(line.peak_line_flux_uncertainty_negative) +\
                                  " New Peak Line Flux Negative Uncertainty: " +\
                                  str(form.peak_line_flux_uncertainty_negative.data)
                if form.line_width.data:
                    if float(line.line_width) != float(form.line_width.data):
                        changes = changes + "Initial Line Width: " + str(line.line_width) + " New Line Width: " +\
                                  str(form.line_width.data)
                if form.line_width_uncertainty_positive.data:
                    if float(line.line_width_uncertainty_positive) != float(form.line_width_uncertainty_positive.data):
                        changes = changes + "Initial Line Width Positive Uncertainty: " +\
                                  str(line.line_width_uncertainty_positive) +\
                                  " New Line Width Positive Uncertainty: " +\
                                  str(form.line_width_uncertainty_positive.data)
                if form.line_width_uncertainty_negative.data:
                    if float(line.line_width_uncertainty_negative) != float(form.line_width_uncertainty_negative.data):
                        changes = changes + "Initial Line Width Negative Uncertainty: " +\
                                  str(line.line_width_uncertainty_negative) +\
                                  " New Line Width Negative Uncertainty: " +\
                                  str(form.line_width_uncertainty_negative.data)
                if form.observed_line_redshift.data:
                    if float(line.observed_line_redshift) != float(form.observed_line_redshift.data):
                        changes = changes + "Initial Observed Line Frequency: " +\
                                  str(line.observed_line_redshift) +\
                                  " New Observed Line Frequency: " +\
                                  str(form.observed_line_redshift.data)
                if form.observed_line_redshift_uncertainty_positive.data:
                    if float(line.observed_line_redshift_uncertainty_positive) != float(
                            form.observed_line_redshift_uncertainty_positive.data):
                        changes = changes + "Initial Observed Line Frequency Positive Uncertainty: " +\
                                  str(line.observed_line_redshift_uncertainty_positive) +\
                                  " New Observed Line Frequency Positive Uncertainty: " +\
                                  str(form.observed_line_redshift_uncertainty_positive.data)
                if form.observed_line_redshift_uncertainty_negative.data:
                    if float(line.observed_line_redshift_uncertainty_negative) != float(
                            form.observed_line_redshift_uncertainty_negative.data):
                        changes = changes + "Initial Observed Line Frequency Negative Uncertainty: " +\
                                  str(line.observed_line_redshift_uncertainty_negative) +\
                                  " New Observed Line Frequency Negative Uncertainty: " +\
                                  str(form.observed_line_redshift_uncertainty_negative.data)
                if form.detection_type.data:
                    if line.detection_type != form.detection_type.data:
                        changes = changes + "Initial Detection Type: " + str(line.detection_type) +\
                                  " New Detection Type: " + form.detection_type.data
                if form.observed_beam_major.data:
                    if float(line.observed_beam_major) != float(form.observed_beam_major.data):
                        changes = changes + "Initial Observed Beam Major: " + str(line.observed_beam_major) +\
                                  " New Observed Beam Major: " + str(form.observed_beam_major.data)
                if form.observed_beam_minor.data:
                    if float(line.observed_beam_minor) != float(form.observed_beam_minor.data):
                        changes = changes + "Initial Observed Beam Minor: " + str(line.observed_beam_minor) +\
                                  " New Observed Beam Minor: " + str(form.observed_beam_minor.data)
                if form.observed_beam_angle.data:
                    if float(line.observed_beam_angle) != float(form.observed_beam_angle.data):
                        changes = changes + "Initial Observed Beam Angle: " + str(line.observed_beam_angle) +\
                                  " New Observed Beam Angle: " + str(form.observed_beam_angle.data)
                if form.reference.data:
                    if line.reference != form.reference.data:
                        changes = changes + "Initial Reference: " + str(line.reference) +\
                                  " New Reference: " + form.reference.data
                if form.notes.data:
                    if line.notes != form.notes.data:
                        changes = changes + "Initial Notes: " + line.notes + " New Notes: " + form.notes.data
                line = EditLine(galaxy_id=galaxy_id, emitted_frequency=form.emitted_frequency.data,
                                species=form.species.data, integrated_line_flux=form.integrated_line_flux.data,
                                integrated_line_flux_uncertainty_positive=form.integrated_line_flux_uncertainty_positive.data,
                                integrated_line_flux_uncertainty_negative=form.integrated_line_flux_uncertainty_negative.data,
                                peak_line_flux=form.peak_line_flux.data,
                                peak_line_flux_uncertainty_positive=form.peak_line_flux_uncertainty_positive.data,
                                peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data,
                                line_width=form.line_width.data,
                                line_width_uncertainty_positive=form.line_width_uncertainty_positive.data,
                                line_width_uncertainty_negative=form.line_width_uncertainty_negative.data,
                                observed_line_redshift=frequency,
                                observed_line_redshift_uncertainty_positive=positive_uncertainty,
                                observed_line_redshift_uncertainty_negative=negative_uncertainty,
                                detection_type=form.detection_type.data,
                                observed_beam_major=form.observed_beam_major.data,
                                observed_beam_minor=form.observed_beam_minor.data,
                                observed_beam_angle=form.observed_beam_angle.data, reference=form.reference.data,
                                notes=form.notes.data, user_submitted=current_user.username,
                                user_email=current_user.email, is_edited=changes)
                db.session.add(line)
                db.session.commit()

                # Add the corresponding post
                editline_id = db.session.query(func.max(EditLine.id)).first()[0]
                post = Post(editline_id=editline_id, galaxy_id=galaxy_id, user_email=current_user.email,
                            time_submitted=datetime.utcnow())
                db.session.add(post)
                db.session.commit()

                flash('Line has been edited. ')
                return redirect(url_for('main.main'))
    return render_template('line_edit_form.html', title='Line Edit Form', form=form)


@bp.route('/galaxies')
def galaxydic():
    """
    A helper route to jsonify the list of galaxies.
    """

    session = Session()
    res1 = session.query(Galaxy)
    res2 = session.query(TempGalaxy)
    list_galaxies = [r.as_dict() for r in res1]
    list_temp_galaxies = [r.as_dict() for r in res2]
    list_galaxies.extend(list_temp_galaxies)
    return jsonify(list_galaxies)


@bp.route('/approvedgalaxies')
def galaxies():
    """
    A helper route to jsonify the list of approved galaxies.
    """

    session = Session()
    res = session.query(Galaxy)
    list_galaxies = [r.as_dict() for r in res]
    return jsonify(list_galaxies)


@bp.route('/process', methods=['POST'])
def process():
    galaxy_name = request.form['galaxy_name']
    if galaxy_name:
        return jsonify({'galaxy_name': galaxy_name})
    return jsonify({'error': 'missing data..'})


@bp.route('/galaxy/<name>', methods=['GET'])
def galaxy(name):
    """
    Galaxy page route

    On GET:
        Parameters:
             name (str): name of the galaxy (unique) under investigation.

        Returns:
            galaxy.html
            galaxy (Galaxy): A db model object under investigation (rounded redshifts + uncertainties).
            lines (db.session.query): Lines that belong to the selected galaxy (rounded redshifts + uncertainties).
    """

    galaxy = Galaxy.query.filter_by(name=name).first_or_404()

    # see round_redshift in helpers.py to see how rounding is performed.
    galaxy.redshift, galaxy.redshift_error, _ = round_redshift(
        galaxy.redshift,
        galaxy.redshift_error,
        galaxy.redshift_error,
        True,
        False
    )

    lines = db.session.query(Line).filter_by(galaxy_id=galaxy.id).all()

    for line in lines:
        line.observed_line_redshift,\
         line.observed_line_redshift_uncertainty_positive,\
         line.observed_line_redshift_uncertainty_negative = round_redshift(
            line.observed_line_redshift,
            line.observed_line_redshift_uncertainty_positive,
            line.observed_line_redshift_uncertainty_negative,
            True,
            False
         )

    return render_template('galaxy.html', galaxy=galaxy, lines=lines)


@bp.route("/submit")
@login_required
def submit():
    return render_template("submit.html")


@bp.route("/test")
@login_required
def test():
    return "test"


@bp.route("/convert_to_CSV/<table>/<identifier>/<to_frequency>", methods=['GET', 'POST'])
@login_required
def convert_to_CSV(table, identifier, to_frequency="0"):
    """
    Converts a query to CSV route

    On GET:
        Parameters:
            table (str): Indicator string that specifies the type of the table desired by the user.
            identifier (str): the id of the galaxy if one.
            to_frequency (str): "0" - return data as redshift (default), "1" - convert to frequency.

        Returns:
            response (flask.make_response): the flask response.
    """

    if request.method == 'GET':
        # convert to_frequency to a boolean
        if int(to_frequency):
            to_frequency = True
            # rename columns accordingly
            observed_line_f_or_z = COL_NAMES['observed_line_frequency']
            observed_line_f_or_z_uncertainty_positive = COL_NAMES['observed_line_frequency_uncertainty_positive']
            observed_line_f_or_z_uncertainty_negative = COL_NAMES['observed_line_frequency_uncertainty_negative']
        else:
            to_frequency = False
            # rename columns accordingly
            observed_line_f_or_z = COL_NAMES['observed_line_redshift']
            observed_line_f_or_z_uncertainty_positive = COL_NAMES['observed_line_redshift_uncertainty_positive']
            observed_line_f_or_z_uncertainty_negative = COL_NAMES['observed_line_redshift_uncertainty_negative']
        if table == "Galaxy":

            # Galaxy takes averaged coordinates
            f = open('galaxy.csv', 'w')
            out = csv.writer(f)
            out.writerow([
                COL_NAMES['name'],
                COL_NAMES['right_ascension_weighted_average'],
                COL_NAMES['declination_weighted_average'],
                COL_NAMES['coordinate_system'],
                COL_NAMES['redshift'],
                COL_NAMES['lensing_flag'],
                COL_NAMES['classification'],
                COL_NAMES['g_notes']
            ])

            for item in Galaxy.query.all():
                out.writerow([
                    item.name,
                    item.right_ascension,
                    item.declination,
                    item.coordinate_system,
                    item.redshift,
                    item.lensing_flag,
                    item.classification,
                    item.notes
                ])
            f.close()
            with open('./galaxy.csv', 'r') as file:
                galaxy_csv = file.read()
            response = make_response(galaxy_csv)
            cd = 'attachment; filename=galaxy.csv'
            response.headers['Content-Disposition'] = cd
            response.mimetype = 'text/csv'
            return response

        elif table == "Line":

            # Line takes individual coordinates
            f = open('line.csv', 'w')
            out = csv.writer(f)
            out.writerow([
                COL_NAMES['right_ascension'],
                COL_NAMES['declination'],
                COL_NAMES['integrated_line_flux'],
                COL_NAMES['integrated_line_flux_uncertainty_positive'],
                COL_NAMES['integrated_line_flux_uncertainty_negative'],
                COL_NAMES['peak_line_flux'],
                COL_NAMES['peak_line_flux_uncertainty_positive'],
                COL_NAMES['peak_line_flux_uncertainty_negative'],
                COL_NAMES['line_width'],
                COL_NAMES['line_width_uncertainty_positive'],
                COL_NAMES['line_width_uncertainty_negative'],
                observed_line_f_or_z,
                observed_line_f_or_z_uncertainty_positive,
                observed_line_f_or_z_uncertainty_negative,
                COL_NAMES['detection_type'],
                COL_NAMES['observed_beam_major'],
                COL_NAMES['observed_beam_minor'],
                COL_NAMES['observed_beam_angle'],
                COL_NAMES['reference'],
                COL_NAMES['l_notes']
            ])
            for item in Line.query.all():
                # convert to frequency on request
                if to_frequency:
                    item.observed_line_redshift,\
                     item.observed_line_redshift_uncertainty_positive,\
                     item.observed_line_redshift_uncertainty_negative = redshift_to_frequency(
                        item.emitted_frequency,
                        item.observed_line_redshift,
                        item.observed_line_redshift_uncertainty_positive,
                        item.observed_line_redshift_uncertainty_negative)
                # round_redshift
                item.observed_line_redshift,\
                 item.observed_line_redshift_uncertainty_positive,\
                 item.observed_line_redshift_uncertainty_negative = round_redshift(
                    item.observed_line_redshift,
                    item.observed_line_redshift_uncertainty_positive,
                    item.observed_line_redshift_uncertainty_negative,
                    not to_frequency,
                    True)
                # write out
                out.writerow([
                    item.integrated_line_flux,
                    item.integrated_line_flux_uncertainty_positive,
                    item.integrated_line_flux_uncertainty_negative,
                    item.peak_line_flux,
                    item.peak_line_flux_uncertainty_positive,
                    item.peak_line_flux_uncertainty_negative,
                    item.line_width,
                    item.line_width_uncertainty_positive,
                    item.line_width_uncertainty_negative,
                    item.observed_line_redshift,
                    item.observed_line_redshift_uncertainty_positive,
                    item.observed_line_redshift_uncertainty_negative,
                    item.detection_type,
                    item.observed_beam_major,
                    item.observed_beam_minor,
                    item.observed_beam_angle,
                    item.reference,
                    item.notes
                ])
            f.close()
            with open('./line.csv', 'r') as file:
                line_csv = file.read()
            response = make_response(line_csv)
            cd = 'attachment; filename=line.csv'
            response.headers['Content-Disposition'] = cd
            response.mimetype = 'text/csv'
            return response

        elif table == "Galaxy Lines":

            # Galaxy with lines takes lines individual coordinates
            f = open('galaxy_lines.csv', 'w')
            out = csv.writer(f)
            galaxy_lines = db.session.query(Galaxy, Line).outerjoin(Galaxy).filter(Galaxy.id == identifier,
                                                                                Line.galaxy_id == identifier)
            out.writerow([
                COL_NAMES['name'],
                COL_NAMES['right_ascension_weighted_average'],
                COL_NAMES['declination_weighted_average'],
                COL_NAMES['coordinate_system'],
                COL_NAMES['redshift'],
                COL_NAMES['lensing_flag'],
                COL_NAMES['classification'],
                COL_NAMES['g_notes'],
                COL_NAMES['right_ascension'],
                COL_NAMES['declination'],
                COL_NAMES['emitted_frequency'],
                COL_NAMES['species'],
                COL_NAMES['integrated_line_flux'],
                COL_NAMES['integrated_line_flux_uncertainty_positive'],
                COL_NAMES['integrated_line_flux_uncertainty_negative'],
                COL_NAMES['peak_line_flux'],
                COL_NAMES['peak_line_flux_uncertainty_positive'],
                COL_NAMES['peak_line_flux_uncertainty_negative'],
                COL_NAMES['line_width'],
                COL_NAMES['line_width_uncertainty_positive'],
                COL_NAMES['line_width_uncertainty_negative'],
                observed_line_f_or_z,
                observed_line_f_or_z_uncertainty_positive,
                observed_line_f_or_z_uncertainty_negative,
                COL_NAMES['detection_type'],
                COL_NAMES['observed_beam_major'],
                COL_NAMES['observed_beam_minor'],
                COL_NAMES['observed_beam_angle'],
                COL_NAMES['reference'],
                COL_NAMES['l_notes']
            ])
            for item in galaxy_lines:
                l = item[1]
                g = item[0]
                # convert to frequency on request
                if to_frequency:
                    l.observed_line_redshift,\
                     l.observed_line_redshift_uncertainty_positive,\
                     l.observed_line_redshift_uncertainty_negative = redshift_to_frequency(
                        l.emitted_frequency,
                        l.observed_line_redshift,
                        l.observed_line_redshift_uncertainty_positive,
                        l.observed_line_redshift_uncertainty_negative)
                # round_redshift
                l.observed_line_redshift,\
                 l.observed_line_redshift_uncertainty_positive,\
                 l.observed_line_redshift_uncertainty_negative = round_redshift(
                    l.observed_line_redshift,
                    l.observed_line_redshift_uncertainty_positive,
                    l.observed_line_redshift_uncertainty_negative,
                    not to_frequency,
                    True)
                # write out
                out.writerow([
                    g.name,
                    g.right_ascension,
                    g.declination,
                    g.coordinate_system,
                    g.redshift,
                    g.lensing_flag,
                    g.classification,
                    g.notes,
                    l.right_ascension,
                    l.declination,
                    l.emitted_frequency,
                    l.species,
                    l.integrated_line_flux,
                    l.integrated_line_flux_uncertainty_positive,
                    l.integrated_line_flux_uncertainty_negative,
                    l.peak_line_flux,
                    l.peak_line_flux_uncertainty_positive,
                    l.peak_line_flux_uncertainty_negative,
                    l.line_width,
                    l.line_width_uncertainty_positive,
                    l.line_width_uncertainty_negative,
                    l.observed_line_redshift,
                    l.observed_line_redshift_uncertainty_positive,
                    l.observed_line_redshift_uncertainty_negative,
                    l.detection_type,
                    l.observed_beam_major,
                    l.observed_beam_minor,
                    l.observed_beam_angle,
                    l.reference,
                    l.notes
                ])
            f.close()
            with open('./galaxy_lines.csv', 'r') as file:
                galaxy_lines_csv = file.read()
            response = make_response(galaxy_lines_csv)
            cd = 'attachment; filename=galaxy_lines.csv'
            response.headers['Content-Disposition'] = cd
            response.mimetype = 'text/csv'
            return response

        elif table == "Everything":

            # Lines take individual coordinates
            f = open('galaxies_lines.csv', 'w')
            out = csv.writer(f)
            data = db.session.query(Galaxy, Line).outerjoin(Line)
            out.writerow([
                COL_NAMES['name'],
                COL_NAMES['right_ascension_weighted_average'],
                COL_NAMES['declination_weighted_average'],
                COL_NAMES['coordinate_system'],
                COL_NAMES['redshift'],
                COL_NAMES['lensing_flag'],
                COL_NAMES['classification'],
                COL_NAMES['g_notes'],
                COL_NAMES['right_ascension'],
                COL_NAMES['declination'],
                COL_NAMES['emitted_frequency'],
                COL_NAMES['species'],
                COL_NAMES['integrated_line_flux'],
                COL_NAMES['integrated_line_flux_uncertainty_positive'],
                COL_NAMES['integrated_line_flux_uncertainty_negative'],
                COL_NAMES['peak_line_flux'],
                COL_NAMES['peak_line_flux_uncertainty_positive'],
                COL_NAMES['peak_line_flux_uncertainty_negative'],
                COL_NAMES['line_width'],
                COL_NAMES['line_width_uncertainty_positive'],
                COL_NAMES['line_width_uncertainty_negative'],
                observed_line_f_or_z,
                observed_line_f_or_z_uncertainty_positive,
                observed_line_f_or_z_uncertainty_negative,
                COL_NAMES['detection_type'],
                COL_NAMES['observed_beam_major'],
                COL_NAMES['observed_beam_minor'],
                COL_NAMES['observed_beam_angle'],
                COL_NAMES['reference'],
                COL_NAMES['l_notes']
            ])
            for item in data:
                l = item[1]
                g = item[0]
                if l is not None:
                    # convert to frequency on request
                    if to_frequency:
                        l.observed_line_redshift, \
                        l.observed_line_redshift_uncertainty_positive, \
                        l.observed_line_redshift_uncertainty_negative = redshift_to_frequency(
                            l.emitted_frequency,
                            l.observed_line_redshift,
                            l.observed_line_redshift_uncertainty_positive,
                            l.observed_line_redshift_uncertainty_negative)
                    # round_redshift
                    l.observed_line_redshift, \
                    l.observed_line_redshift_uncertainty_positive, \
                    l.observed_line_redshift_uncertainty_negative = round_redshift(
                        l.observed_line_redshift,
                        l.observed_line_redshift_uncertainty_positive,
                        l.observed_line_redshift_uncertainty_negative,
                        not to_frequency,
                        True)
                    # write out
                    out.writerow([
                        g.name,
                        g.right_ascension,
                        g.declination,
                        g.coordinate_system,
                        g.redshift,
                        g.lensing_flag,
                        g.classification,
                        g.notes,
                        l.right_ascension,
                        l.declination,
                        l.emitted_frequency,
                        l.species,
                        l.integrated_line_flux,
                        l.integrated_line_flux_uncertainty_positive,
                        l.integrated_line_flux_uncertainty_negative,
                        l.peak_line_flux,
                        l.peak_line_flux_uncertainty_positive,
                        l.peak_line_flux_uncertainty_negative,
                        l.line_width,
                        l.line_width_uncertainty_positive,
                        l.line_width_uncertainty_negative,
                        l.observed_line_redshift,
                        l.observed_line_redshift_uncertainty_positive,
                        l.observed_line_redshift_uncertainty_negative,
                        l.detection_type,
                        l.observed_beam_major,
                        l.observed_beam_minor,
                        l.observed_beam_angle,
                        l.reference,
                        l.notes
                    ])
                else:
                    out.writerow([
                        g.name,
                        g.right_ascension,
                        g.declination,
                        g.coordinate_system,
                        g.redshift,
                        g.lensing_flag,
                        g.classification,
                        g.notes
                    ])
            f.close()
            with open('./galaxies_lines.csv', 'r') as file:
                galaxies_lines_csv = file.read()
            response = make_response(galaxies_lines_csv)
            cd = 'attachment; filename=galaxies_lines.csv'
            response.headers['Content-Disposition'] = cd
            response.mimetype = 'text/csv'
            return response
        elif table == "Empty":
            f = open('sample.csv', 'w')
            out = csv.writer(f)
            out.writerow([
                COL_NAMES['name'],
                COL_NAMES['coordinate_system'],
                COL_NAMES['lensing_flag'],
                COL_NAMES['classification'],
                COL_NAMES['g_notes'],
                COL_NAMES['right_ascension'],
                COL_NAMES['declination'],
                COL_NAMES['emitted_frequency'],
                COL_NAMES['species'],
                COL_NAMES['integrated_line_flux'],
                COL_NAMES['integrated_line_flux_uncertainty_positive'],
                COL_NAMES['integrated_line_flux_uncertainty_negative'],
                COL_NAMES['peak_line_flux'],
                COL_NAMES['peak_line_flux_uncertainty_positive'],
                COL_NAMES['peak_line_flux_uncertainty_negative'],
                COL_NAMES['line_width'],
                COL_NAMES['line_width_uncertainty_positive'],
                COL_NAMES['line_width_uncertainty_negative'],
                COL_NAMES['observed_line_redshift'],
                COL_NAMES['observed_line_redshift_uncertainty_positive'],
                COL_NAMES['observed_line_redshift_uncertainty_negative'],
                COL_NAMES['detection_type'],
                COL_NAMES['observed_beam_major'],
                COL_NAMES['observed_beam_minor'],
                COL_NAMES['observed_beam_angle'],
                COL_NAMES['reference'],
                COL_NAMES['l_notes']
            ])
            f.close()
            with open('./sample.csv', 'r') as file:
                sample_csv = file.read()
            response = make_response(sample_csv)
            cd = 'attachment; filename=sample.csv'
            response.headers['Content-Disposition'] = cd
            response.mimetype = 'text/csv'
            return response
