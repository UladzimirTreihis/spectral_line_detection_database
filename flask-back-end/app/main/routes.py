from operator import ne
from flask.globals import session
from sqlalchemy.sql.expression import outerjoin, true
from app import db, Session, engine
from flask import render_template, flash, redirect, url_for, request, g, make_response, jsonify, json
from app.models import Galaxy, User, Line, TempGalaxy, TempLine, Post, EditGalaxy, EditLine
from app.main.forms import EditProfileForm, SearchForm, AddGalaxyForm, EditGalaxyForm, AddLineForm, EditLineForm, AdvancedSearchForm, UploadFileForm
from werkzeug.urls import url_parse
import csv
from sqlalchemy import func
from sqlalchemy.sql import text
from config import EMITTED_FREQUENCY, COL_NAMES, ra_reg_exp, dec_reg_exp
from io import TextIOWrapper
from flask_security import current_user, login_required, roles_required
import math
from app.main import bp
import re
from datetime import datetime

@bp.route("/")
@bp.route("/home")
def home():

    ''' Home page route '''

    return render_template("/home.html")

@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():

    ''' 
    Edit profile route
    
    On access: returns the form with prefilled user's data
    On submit: Updates user's data and returns /main 
    '''

    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.university = form.university.data
        current_user.website = form.website.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash ("Your changes have been submitted")
        return redirect(url_for('main.main'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.university.data = current_user.university
        form.website.data = current_user.website
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form, user=user)

@bp.route('/test')
@roles_required('Admin') 
@login_required
def test():

    ''' Test route, used for development purposes only '''

    session = Session()
    galaxies = session.query(Galaxy).filter(text('cos(Galaxy.declination)<0.8')).all()
    return render_template("/test.html", galaxies=galaxies)

@bp.route("/main", methods=['GET', 'POST'])
@login_required
def main():
    
    '''
    Main route

    On authenticated access: returns main menu and table with galaxy data
    '''

    if current_user.is_authenticated:
        form = SearchForm()
    return render_template("/main.html", galaxy = Galaxy.query.all(), line = Line.query.all(), form=form)

def to_empty(entry):
    
    '''
    Converts None values to empty strings. If value != None, then value=value
    '''
    
    if entry == None:
        entry = ''
    else:
        entry = entry
    return entry

def to_none(entry):

    '''
    Converts empty strings to None. If value != '', then value=value
    '''
    
    if entry == '':
        entry = None
    else:
        entry = float(entry)
    return entry

def to_m_inf(entry):
    
    '''
    Converts empty strings or None values to -inf. 
    If value != '', or value != None, then value=value
    '''
    
    if entry == None:
        entry = float('-inf')
    elif entry == '':
        entry = '-inf'
    else:
        entry = entry
    return entry

def to_p_inf(entry):

    '''
    Converts empty strings or None values to inf. 
    If value != '', or value != None, then value=value
    '''

    if entry == None:
        entry = float('inf')
    elif entry == '':
        entry = 'inf'
    else:
        entry = entry
    return entry

def to_zero(entry):

    '''
    Converts None values to 0. 
    If value != None, then value=value
    '''

    if entry == None:
        entry = 0
    else:
        entry = entry
    return entry


def within_distance(session, query, form_ra, form_dec, distance = 0, based_on_beam_angle = False):
    
    '''
    Takes in a point's coordinates \form_ra and \form_dec and a \distance to check if any galaxy from \query is within the \distance.
    Employs Great-circle distance: https://en.wikipedia.org/wiki/Great-circle_distance
    If the \distance is not provided, it is assumed to be 3 * Line.observed_beam_minor.
    If Line.observed_beam_minor is not available, the distance is assumed to be 5 arcsec to be in an extreme proximity. 

    Returns:
    galaxies -- a query object containing all galaxies that satisfy the distance formula. 

    Parameters:
    session -- the session in which the \query is evoked is passed.

    query -- predefined query object is passed containing galaxies that are to be considered in terms of their proximity 
    to some point/galaxy with given coordinates. It has to contain the Galaxy & Line table data if the distance is not passed and \based_on_beam_angle == True
    
    form_ra -- right ascension of a point/galaxy
    form_dec -- declination of a point/galaxy
    distance -- circular distance away from the point with coordinates (\form_ra, \form_dec). (default 0)
    based_on_beam_angle -- Boolean value to check whether user wants to search for galaxies with extreme proximity based on their Line.observed_beam_minor.
    (default False)


    '''

    if based_on_beam_angle == False:
        galaxies=query.filter(func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < distance)
        return galaxies
    else:
        subqry = session.query(func.max(Line.observed_beam_angle))
        sub = subqry.first()
        sub1 = sub[0]
        if sub1  != None:
            galaxies=query.filter(((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < (func.radians(subqry))/1200) & (subqry != None)) | (func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < func.radians(5/3600)) )   
        else:
            galaxies=query.filter((func.acos(func.sin(func.radians(ra_to_float(form_ra))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_ra))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_dec) - Galaxy.declination)))   ) < func.radians(5/3600)) )
        return galaxies
    


#Is expected to redirect here to display the results. 
@bp.route("/query_results", methods=['GET', 'POST'])
@login_required
def query_results():
    form = SearchForm()
    form_advanced = AdvancedSearchForm()
    conn = engine.connect()    
    session = Session(bind=conn)
    
    if form_advanced.validate_on_submit():

        if form_advanced.name.data == None:
            form_advanced.name.data = ''
        if form_advanced.redshift_min.data == None:
            form_advanced.redshift_min.data = float('-inf')
        if form_advanced.redshift_max.data == None:
            form_advanced.redshift_max.data = float('inf')
        if form_advanced.lensing_flag.data == None or form_advanced.lensing_flag.data == 'Either':
            form_advanced.lensing_flag.data = ''
        if form_advanced.j_upper_min.data == None:
            form_advanced.j_upper_min.data = float('-inf')
        if form_advanced.j_upper_max.data == None:
            form_advanced.j_upper_max.data = float('inf')
        if form_advanced.integrated_line_flux_min.data == None:
            form_advanced.integrated_line_flux_min.data = float('-inf')
        if form_advanced.integrated_line_flux_max.data == None:
            form_advanced.integrated_line_flux_max.data = float('inf')
        if form_advanced.peak_line_flux_min.data == None:
            form_advanced.peak_line_flux_min.data = float('-inf')
        if form_advanced.peak_line_flux_max.data == None:
            form_advanced.peak_line_flux_max.data = float('inf')
        if form_advanced.line_width_min.data == None:
            form_advanced.line_width_min.data = float('-inf')
        if form_advanced.line_width_max.data == None:
            form_advanced.line_width_max.data = float('inf')
        if form_advanced.observed_line_frequency_min.data == None:
            form_advanced.observed_line_frequency_min.data = float('-inf')
        if form_advanced.observed_line_frequency_max.data == None:
            form_advanced.observed_line_frequency_max.data = float('inf')
        if form_advanced.detection_type.data == None or form_advanced.detection_type.data == 'Either':
            form_advanced.detection_type.data = ''
        if form_advanced.observed_beam_major_min.data == None:
            form_advanced.observed_beam_major_min.data = float('-inf')
        if form_advanced.observed_beam_major_max.data == None:
            form_advanced.observed_beam_major_max.data = float('inf')
        if form_advanced.observed_beam_minor_min.data == None:
            form_advanced.observed_beam_minor_min.data = float('-inf')
        if form_advanced.observed_beam_minor_max.data == None:
            form_advanced.observed_beam_minor_max.data = float('inf')
        if form_advanced.reference.data == None:
            form_advanced.reference.data = ''
        
        #query displaying galaxies based on the data from form_advanced


        if form_advanced.galaxySearch.data:
            
            #Additional filter if radius is specified
            if (form_advanced.right_ascension_point.data != None) and (form_advanced.declination_point.data != None) and ((form_advanced.radius_d.data != None) or (form_advanced.radius_m.data != None) or (form_advanced.radius_s.data != None)):
                distance=math.radians(to_zero(form_advanced.radius_d.data)+to_zero(form_advanced.radius_m.data)/60+to_zero(form_advanced.radius_s.data)/3600) 
                galaxies=session.query(Galaxy, Line).outerjoin(Line)
                galaxies = within_distance(session, galaxies, form_advanced.right_ascension_point.data, form_advanced.declination_point.data, distance=distance)
                
            else:
                galaxies=session.query(Galaxy, Line).outerjoin(Line)

            #Filters in respect to galaxy parameters
            galaxies=galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)), ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (Galaxy.declination.between(dec_to_float(to_m_inf(form_advanced.declination_min.data)), dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data) | (Galaxy.redshift == None) ) & (Galaxy.lensing_flag.contains(form_advanced.lensing_flag.data) | (Galaxy.lensing_flag == None)))

            #Filters in respect to line parameters or if galaxy has no lines
            galaxies = galaxies.filter((Line.id == None) | ((Line.j_upper.between(form_advanced.j_upper_min.data, form_advanced.j_upper_max.data) | (Line.j_upper == None )) & (Line.integrated_line_flux.between(form_advanced.integrated_line_flux_min.data, form_advanced.integrated_line_flux_max.data) | (Line.integrated_line_flux == None)) & (Line.peak_line_flux.between(form_advanced.peak_line_flux_min.data, form_advanced.peak_line_flux_max.data) | (Line.peak_line_flux == None)) & (Line.line_width.between(form_advanced.line_width_min.data, form_advanced.line_width_max.data) | (Line.line_width == None )) & (Line.observed_line_frequency.between(form_advanced.observed_line_frequency_min.data, form_advanced.observed_line_frequency_max.data) | (Line.observed_line_frequency == None )) & (Line.detection_type.contains(form_advanced.detection_type.data) | (Line.detection_type == None)) & (Line.observed_beam_major.between(form_advanced.observed_beam_major_min.data, form_advanced.observed_beam_major_max.data) | (Line.observed_beam_major == None )) & (Line.observed_beam_minor.between(form_advanced.observed_beam_minor_min.data, form_advanced.observed_beam_minor_max.data) | (Line.observed_beam_minor == None )) & (Line.reference.contains(form_advanced.reference.data) | (Line.reference == None)) ))

            galaxies = galaxies.distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()

            return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)   

            
        
        elif form_advanced.lineSearch.data:
            if (form_advanced.right_ascension_point.data != None) and (form_advanced.declination_point.data != None) and ((form_advanced.radius_d.data != None) or (form_advanced.radius_m.data != None) or (form_advanced.radius_s.data != None)):
                distance=math.radians(to_zero(form_advanced.radius_d.data)+to_zero(form_advanced.radius_m.data)/60+to_zero(form_advanced.radius_s.data)/3600) 
                galaxies=session.query(Galaxy, Line).outerjoin(Galaxy)
                galaxies = within_distance(session, galaxies, form_advanced.right_ascension_point.data, form_advanced.declination_point.data, distance=distance)
                
            else:
                galaxies=session.query(Galaxy, Line).outerjoin(Galaxy)


            galaxies=galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)), ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (Galaxy.declination.between(dec_to_float(to_m_inf(form_advanced.declination_min.data)), dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data) | (Galaxy.redshift == None) ) & (Galaxy.lensing_flag.contains(form_advanced.lensing_flag.data) | (Galaxy.lensing_flag == None)))

            galaxies=galaxies.filter((Line.j_upper.between(form_advanced.j_upper_min.data, form_advanced.j_upper_max.data) | (Line.j_upper == None )) & (Line.integrated_line_flux.between(form_advanced.integrated_line_flux_min.data, form_advanced.integrated_line_flux_max.data) | (Line.integrated_line_flux == None)) & (Line.peak_line_flux.between(form_advanced.peak_line_flux_min.data, form_advanced.peak_line_flux_max.data) | (Line.peak_line_flux == None)) & (Line.line_width.between(form_advanced.line_width_min.data, form_advanced.line_width_max.data) | (Line.line_width == None )) & (Line.observed_line_frequency.between(form_advanced.observed_line_frequency_min.data, form_advanced.observed_line_frequency_max.data) | (Line.observed_line_frequency == None )) & (Line.detection_type.contains(form_advanced.detection_type.data) | (Line.detection_type == None)) & (Line.observed_beam_major.between(form_advanced.observed_beam_major_min.data, form_advanced.observed_beam_major_max.data) | (Line.observed_beam_major == None )) & (Line.observed_beam_minor.between(form_advanced.observed_beam_minor_min.data, form_advanced.observed_beam_minor_max.data) | (Line.observed_beam_minor == None )) & (Line.reference.contains(form_advanced.reference.data) | (Line.reference == None)) )
            
            galaxies=galaxies.order_by(Galaxy.name).all()

            return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)

        #don't need if we take away the general search bar    
        #elif form.submit:
            #galaxies = Galaxy.query.filter(Galaxy.name.contains(form.search.data) | Galaxy.notes.contains(form.search.data))
        else:
            galaxies = session.query(Galaxy, Line).outerjoin(Line).distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()
        return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)
    
    else:
        galaxies = session.query(Galaxy, Line).outerjoin(Line).distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()
    
    return render_template("/query_results.html", form=form, form_advanced=form_advanced, galaxies=galaxies)

@bp.route("/entry_file", methods=['GET', 'POST'])
@login_required
def entry_file():
    form = UploadFileForm()
    if request.method == 'POST':
        csvfile = request.files['file']
        csv_file = TextIOWrapper(csvfile, encoding='windows-1252')
        reader = csv.DictReader(csv_file)
        data = [row for row in reader]
        if data == []:
            flash ("CSV File is empty. ")
        g_validated = True
        for row in data:
            if row == []:
                flash ('that was an empty row')
                continue
            if row[COL_NAMES['name']] == "":
                g_validated = False
                flash ("Galaxy Name is Mandatory")
            if row[COL_NAMES['coordinate_system']] != "ICRS" and row[COL_NAMES['coordinate_system']] != "J2000":
                g_validated = False
                flash ("Coordinate System can be ICRS or J2000 only.")
            if row[COL_NAMES['lensing_flag']] != "Lensed" and row[COL_NAMES['lensing_flag']] != "Unlensed" and row[COL_NAMES['lensing_flag']] != "l" and row[COL_NAMES['lensing_flag']] != "u":
                g_validated = False
                flash ("Please enter either \"Lensed\", \"Unlensed\" or \"Either\", \"u\" under {}.".format(COL_NAMES['lensing_flag']))
            if row[COL_NAMES['classification']] == "":
                g_validated = False
                flash ("Classification is Mandatory")
            if row[COL_NAMES['right_ascension']] == "":
                g_validated = False
                flash ("Right Ascension is Mandatory")
            if re.search(ra_reg_exp, row[COL_NAMES['right_ascension']]) == None:
                g_validated = False
                flash ("Enter Right Ascension in a proper format")
            if row[COL_NAMES['declination']] == "":
                g_validated = False
                flash ("Declination is Mandatory")
            if re.search(dec_reg_exp, row[COL_NAMES['declination']]) == None:
                g_validated = False
                flash ("Enter Declination in a proper format")
            if g_validated == True:
                ra = ra_to_float(row[COL_NAMES['right_ascension']])
                dec = dec_to_float(row[COL_NAMES['declination']])
                name = row[COL_NAMES['name']]
                check_same_temp_galaxy = db.session.query(TempGalaxy.id).filter((TempGalaxy.right_ascension == ra) & (TempGalaxy.declination == dec) & (TempGalaxy.name == name))
                check_same_galaxy = db.session.query(Galaxy.id).filter((Galaxy.right_ascension == ra) & (Galaxy.declination == dec) & (Galaxy.name == name))
                if (check_same_temp_galaxy.first() == None) & (check_same_galaxy.first() == None):
                    #galaxies=session.query(Galaxy, Line).outerjoin(Line)
                    #galaxies = within_distance(session, galaxies, RA, DEC, based_on_beam_angle=True)
                    #galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)
                    galaxy = TempGalaxy(name = row['name'],
                                        right_ascension = ra,
                                        declination = dec,
                                        coordinate_system = row[COL_NAMES['coordinate_system']],
                                        lensing_flag = row [COL_NAMES['lensing_flag']],
                                        classification = row[COL_NAMES ['classification']],
                                        notes = row [COL_NAMES['g_notes']],
                                        user_submitted = current_user.username,
                                        user_email = current_user.email,
                                        time_submitted = datetime.utcnow)
                    db.session.add(galaxy)
                    new_id = db.session.query(func.max(TempGalaxy.id)).first()
                    id = new_id [0]
                    from_existed = None
                elif (check_same_temp_galaxy.first() != None) & (check_same_galaxy.first() == None):
                    new_id = check_same_temp_galaxy.first()
                    id = new_id [0]
                    from_existed = None
                else:
                    new_id = check_same_galaxy.first()
                    id = new_id [0]
                    from_existed = id
                l_validated = True
                if row[COL_NAMES['j_upper']] == "":
                    l_validated = False
                    flash ("J Upper is Mandatory")
                if row[COL_NAMES['integrated_line_flux']] == "":
                    l_validated = False
                    flash ("Integrated Line Flux is Mandatory")
                if row[COL_NAMES['integrated_line_flux_uncertainty_positive']] == "":
                    l_validated = False
                    flash ("Integrated Line Flux Positive Uncertainty is Mandatory")
                if row[COL_NAMES['integrated_line_flux_uncertainty_negative']] == "":
                    l_validated = False
                    flash ("Integrated Line Flux Negative Uncertainty is Mandatory")
                if row [COL_NAMES['integrated_line_flux_uncertainty_positive']] != "":
                    try:
                        if float (row[COL_NAMES['integrated_line_flux_uncertainty_positive']]) < 0:
                            l_validated = False
                            flash ("Integrated Line Flux Positive Uncertainty must be greater than 0")
                    except:
                        pass
                if row [COL_NAMES['integrated_line_flux_uncertainty_negative']] != "":
                    try:
                        if float (row[COL_NAMES['integrated_line_flux_uncertainty_negative']]) < 0:
                            l_validated = False
                            flash ("Integrated Line Flux Negative Uncertainty must be greater than 0")
                    except:
                        pass
                if row [COL_NAMES['peak_line_flux_uncertainty_positive']] != "":
                    try:
                        if float (row [COL_NAMES['peak_line_flux_uncertainty_positive']]) < 0:
                            l_validated = False
                            flash ("Peak Line Flux Positive Uncertainty must be greater than 0")
                    except:
                        pass                
                if row [COL_NAMES['peak_line_flux_uncertainty_negative']] != "":
                    try:
                        if float (row [COL_NAMES['peak_line_flux_uncertainty_negative']]) < 0:
                            l_validated = False
                            flash ("Peak Line Flux Negative Uncertainty must be greater than 0")
                    except:
                        pass
                if row [COL_NAMES['line_width_uncertainty_positive']] != "":
                    try:
                        if float (row [COL_NAMES['line_width_uncertainty_positive']]) < 0:
                            l_validated = False
                            flash ("Line Width Positive Uncertainty must be greater than 0")
                    except:
                        pass
                if row [COL_NAMES['line_width_uncertainty_negative']] != "":
                    try:
                        if float (row [COL_NAMES['line_width_uncertainty_negative']]) < 0:
                            l_validated = False
                            flash ("Line Width Negative Uncertainty must be greater than 0")
                    except:
                        pass
                if row[COL_NAMES['freq_type']] != "z" and row[COL_NAMES['freq_type']] != "f" and row[COL_NAMES['freq_type']] != "":
                    l_validated = False
                    flash ("Please enter either \"z\", \"f\" under {}.".format(COL_NAMES['freq_type']))
                if row [COL_NAMES['observed_line_frequency_uncertainty_positive']] != "":
                    try:
                        if float (row [COL_NAMES['observed_line_frequency_uncertainty_positive']]) < 0:
                            l_validated = False
                            flash ("Observed Line Frequency Positive Uncertainty must be greater than 0")
                    except:
                        pass
                if row [COL_NAMES['observed_line_frequency_uncertainty_negative']] != "":
                    try:
                        if float (row [COL_NAMES['observed_line_frequency_uncertainty_negative']]) < 0:
                            l_validated = False
                            flash ("Observed Line Frequency Negative Uncertainty must be greater than 0")
                    except:
                        pass
                if l_validated == True:
                    if row[COL_NAMES['freq_type']] == "z":
                        frequency, positive_uncertainty = redshift_to_frequency(to_none(row ['j_upper']), to_none( row ['observed_line_frequency']), to_none( row ['line_width_uncertainty_positive']), to_none( row ['line_width_uncertainty_negative']))
                        negative_uncertainty = None
                    else:
                        frequency = to_none( row ['observed_line_frequency'])
                        positive_uncertainty = to_none( row ['line_width_uncertainty_positive'])
                        negative_uncertainty = to_none( row ['line_width_uncertainty_negative'])
                    line = TempLine (galaxy_id = id,
                                    from_existed_id = from_existed,
                                    j_upper= to_none(row ['j_upper']), 
                                    integrated_line_flux =to_none( row ['integrated_line_flux']), 
                                    integrated_line_flux_uncertainty_positive =to_none( row ['integrated_line_flux_uncertainty_positive']), 
                                    integrated_line_flux_uncertainty_negative =to_none( row ['integrated_line_flux_uncertainty_negative']), 
                                    peak_line_flux =to_none( row ['peak_line_flux']),
                                    peak_line_flux_uncertainty_positive =to_none( row ['peak_line_flux_uncertainty_positive']),
                                    peak_line_flux_uncertainty_negative=to_none( row ['peak_line_flux_uncertainty_negative']), 
                                    line_width=to_none( row ['line_width']),
                                    line_width_uncertainty_positive =to_none( row ['line_width_uncertainty_positive']),
                                    line_width_uncertainty_negative =to_none( row ['line_width_uncertainty_negative']),
                                    observed_line_frequency =frequency,
                                    observed_line_frequency_uncertainty_positive =positive_uncertainty,
                                    observed_line_frequency_uncertainty_negative =negative_uncertainty,
                                    detection_type = row ['detection_type'],
                                    observed_beam_major =to_none( row ['observed_beam_major']), 
                                    observed_beam_minor =to_none( row ['observed_beam_minor']),
                                    observed_beam_angle =to_none( row ['observed_beam_angle']),
                                    reference = row ['reference'],
                                    notes = row ['notes'],
                                    user_submitted = current_user.username,
                                    user_email = current_user.email,
                                    time_submitted = datetime.utcnow
                                    )                
                    db.session.add(line)
                    db.session.commit()
                    flash ("File has been successfully uploaded. ")
    return render_template ("/entry_file.html", title = "Upload File", form = form)

def ra_to_float(coordinates):
    if isinstance(coordinates, float) or isinstance(coordinates, int):
        coordinates = str(coordinates)
    if coordinates.find('s') != -1:
        h = float(coordinates[0:2])                      
        m = float(coordinates[3:5])
        s = float(coordinates[coordinates.find('m')+1:coordinates.find('s')])
        return h*15+m/4+s/240
    else:
        return float(coordinates) 
def dec_to_float(coordinates):
    if isinstance(coordinates, float) or isinstance(coordinates, int):
        coordinates = str(coordinates)
    if coordinates.find('s') != -1:
        d = float(coordinates[1:3])
        m = float(coordinates[4:6])
        s = float(coordinates[coordinates.find('m')+1:coordinates.find('s')])
        if coordinates[0] == "-":
            return (-1)*(d+m/60+s/3600)
        else:
            return d+m/60+s/3600
    elif coordinates == '-inf' or coordinates == 'inf':
        return float(coordinates)
    else:
        if coordinates[0] == '+':
            dec = coordinates.replace("+","")
        else:
            dec = coordinates
        return float(dec)

@bp.route("/galaxy_entry_form", methods=['GET', 'POST'])
@login_required
def galaxy_entry_form():
    form = AddGalaxyForm()
    session=Session()
    if form.validate_on_submit ():
        if form.submit_anyway.data:
            try:
                DEC = dec_to_float(form.declination.data)
            except:
                DEC = form.declination.data
            try:
                RA = ra_to_float(form.right_ascension.data)
            except:
                RA = form.right_ascension.data 
            galaxies=session.query(Galaxy, Line).outerjoin(Line)
            galaxies = within_distance(session, galaxies, RA, DEC, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)
            galaxy = TempGalaxy(name=form.name.data, right_ascension=RA, declination = DEC, coordinate_system = form.coordinate_system.data, classification = form.classification.data, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_similar = str(galaxies.all()), time_submitted = datetime.utcnow)
            db.session.add(galaxy)
            db.session.commit()
            tempgalaxy = session.query(TempGalaxy).filter_by(name=form.name.data).first()
            tempgalaxy_id = int(tempgalaxy.repr())
            post = Post(tempgalaxy_id=tempgalaxy_id, user_email = current_user.email, time_submitted = datetime.utcnow)
            db.session.add(post)
            db.session.commit()
            flash ('Galaxy has been added. ')
        if form.do_not_submit.data:
            return redirect (url_for ('main.main'))
        if form.submit.data:
            try:
                DEC = dec_to_float(form.declination.data)
            except:
                DEC = form.declination.data
            try:
                RA = ra_to_float(form.right_ascension.data)
            except:
                RA = form.right_ascension.data 
            galaxies=session.query(Galaxy, Line).outerjoin(Line)
            galaxies = within_distance(session, galaxies, RA, DEC, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)
            if galaxies.first() != None:
                return render_template('galaxy_entry_form.html', title= 'Galaxy Entry Form', form=form, galaxies=galaxies, another_exists=True)
            galaxy = TempGalaxy(name=form.name.data, right_ascension=RA, declination = DEC, coordinate_system = form.coordinate_system.data, classification = form.classification.data, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_similar = None, time_submitted = datetime.utcnow())
            db.session.add(galaxy)
            db.session.commit()
            tempgalaxy = TempGalaxy.query.filter_by(name=form.name.data).first()
            tempgalaxy_id = int(tempgalaxy.__repr__())
            post = Post(tempgalaxy_id=tempgalaxy_id, user_email = current_user.email, time_submitted = datetime.utcnow())
            db.session.add(post)
            db.session.commit()
            flash ('Galaxy has been added. ')
        if form.new_line.data:
            return redirect(url_for('main.line_entry_form'))
    return render_template('galaxy_entry_form.html', title= 'Galaxy Entry Form', form=form)

@bp.route("/galaxy_edit_form/<glist>", methods=['GET', 'POST'])
@login_required
def galaxy_edit_form(glist):
    glist = glist[1: (len(glist) - 2)]
    glist = glist.replace("'","")
    glist = glist.split(",")
    length = len (glist)
    if length > 7:
        for element in range (7, length):
            glist[6] += ","
            glist[6] += (glist[element])
    form = EditGalaxyForm(name = glist[0], right_ascension = float(glist[1]), declination = float(glist[2]), coordinate_system = glist[3], lensing_flag = glist[4], classification = glist[5], notes = glist[6])
    session=Session()
    original = glist[0]
    if form.validate_on_submit ():
        if form.submit_anyway.data:
            try:
                DEC = dec_to_float(form.declination.data)
            except:
                DEC = float(form.declination.data)
            try:
                RA = ra_to_float(form.right_ascension.data)
            except:
                RA = float(form.right_ascension.data)
            galaxies=session.query(Galaxy, Line).outerjoin(Line)
            galaxies = within_distance(session, galaxies, RA, DEC, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)
            changes = ""
            if (glist[0] != form.name.data):
                changes = changes + 'Initial Name: ' + glist [0] + ' New Name:' + form.name.data
            if (str (glist[1]) != str(RA)):
                changes = changes + 'Initial RA: ' + str (glist [1]) + ' New RA:' + str (RA)
            if (str (glist[2]) != str (DEC)):
                changes = changes + 'Initial DEC: ' + str (glist [2]) + ' New DEC:' + str (DEC)
            if (glist[3] != form.coordinate_system.data):
                changes = changes + 'Initial Coordinate System: ' + glist [3] + ' New Coordinate System:' + form.coordinate_system.data
            if (glist[4] != form.lensing_flag.data):
                changes = changes + 'Initial Lensing Flag: ' + glist [5] + ' New Lensing Flag:' + form.lensing_flag.data
            if (glist[5] != form.classification.data):
                changes = changes + 'Initial Classification: ' + glist [4] + ' New Classification:' + form.classification.data
            if (glist[6] != form.notes.data):
                changes = changes + 'Initial Notes: ' + glist [6] + 'New Notes:' + form.notes.data
            galaxy = EditGalaxy(name=form.name.data, right_ascension=RA, declination = DEC, coordinate_system = form.coordinate_system.data, classification = form.classification.data, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_similar = str(galaxies.all()), is_edited = changes, original_id = original)
            db.session.add(galaxy)
            db.session.commit()
            flash ('Galaxy has been Edited. ')
        if form.do_not_submit.data:
            return redirect (url_for ('main.main'))
        if form.submit.data:
            try:
                DEC = dec_to_float(form.declination.data)
            except:
                DEC = form.declination.data
            try:
                RA = ra_to_float(form.right_ascension.data)
            except:
                RA = form.right_ascension.data 
            galaxies=session.query(Galaxy, Line).outerjoin(Line)
            galaxies = within_distance(session, galaxies, RA, DEC, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)
            if galaxies.first() != None:
                return render_template('galaxy_edit_form.html', title= 'Galaxy Edit Form', form=form, galaxies=galaxies, another_exists=True)
            galaxy = EditGalaxy(name=form.name.data, right_ascension=RA, declination = DEC, coordinate_system = form.coordinate_system.data, classification = form.classification.data, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_edited = "Yes")
            db.session.add(galaxy)
            db.session.commit()
            flash ('Galaxy has been Edited. ')
        if form.new_line.data:
            return redirect(url_for('main.line_entry_form'))
    return render_template('galaxy_edit_form.html', title= 'Galaxy Edit Form', form=form)

def update_redshift(session, galaxy_id):
    line_redshift = session.query(
            Line.j_upper, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
        ).outerjoin(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).all() 

    sum_upper = sum_lower = 0
    for l in line_redshift:
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

    redshift_weighted = sum_upper / sum_lower
    session.query(Galaxy).filter(
        Galaxy.id == galaxy_id
    ).update({"redshift": redshift_weighted})
    session.commit()
    
    return sum_upper

def update_redshift_error(session, galaxy_id, sum_upper):
    redshift_error_weighted = 0
    line_redshift = session.query(
            Line.j_upper, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
        ).outerjoin(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).all() 
    for l in line_redshift:
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

def redshift_to_frequency(J_UPPER, z, positive_uncertainty, negative_uncertainty):
    if z == None:
        return None, None
    nu_obs = (EMITTED_FREQUENCY.get(J_UPPER))/(z+1)
    if positive_uncertainty == None:
        return nu_obs, None
    if negative_uncertainty == None:
        negative_uncertainty = positive_uncertainty
    delta_z = positive_uncertainty + negative_uncertainty
    delta_nu = delta_z * nu_obs / (z+1)
    return nu_obs, delta_nu/2




@bp.route("/line_entry_form", methods=['GET', 'POST'])
@login_required
def line_entry_form():
    form = AddLineForm()
    if form.galaxy_form.data:
        return redirect(url_for('main.galaxy_entry_form'))
    if form.validate_on_submit():
        if form.submit.data:
            session = Session()
            galaxy_id = session.query(Galaxy.id).filter(Galaxy.name==form.galaxy_name.data).first()
            try:
                id = galaxy_id[0]
            except:
                id = None
            existed = id

            if galaxy_id == None:
                galaxy_id = session.query(TempGalaxy.id).filter(TempGalaxy.name==form.galaxy_name.data).first()
                id = galaxy_id[0]
                existed = None
            if galaxy_id==None:
                raise Exception ('Please enter the name exactly as proposed using Caps if necesarry')

            if form.freq_type.data == 'z':
                frequency, positive_uncertainty = redshift_to_frequency(form.j_upper.data, form.observed_line_frequency.data, form.observed_line_frequency_uncertainty_positive.data, form.observed_line_frequency_uncertainty_negative.data)
                negative_uncertainty = None
            else:
                frequency = form.observed_line_frequency.data
                positive_uncertainty = form.observed_line_frequency_uncertainty_positive.data
                negative_uncertainty = form.observed_line_frequency_uncertainty_negative.data
            line = TempLine(galaxy_id=id, j_upper=form.j_upper.data, integrated_line_flux = form.integrated_line_flux.data, integrated_line_flux_uncertainty_positive = form.integrated_line_flux_uncertainty_positive.data, integrated_line_flux_uncertainty_negative = form.integrated_line_flux_uncertainty_negative.data, peak_line_flux = form.peak_line_flux.data, peak_line_flux_uncertainty_positive = form.peak_line_flux_uncertainty_positive.data, peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data, line_width=form.line_width.data, line_width_uncertainty_positive = form.line_width_uncertainty_positive.data, line_width_uncertainty_negative = form.line_width_uncertainty_negative.data, observed_line_frequency = frequency, observed_line_frequency_uncertainty_positive = positive_uncertainty, observed_line_frequency_uncertainty_negative = negative_uncertainty, detection_type = form.detection_type.data, observed_beam_major = form.observed_beam_major.data, observed_beam_minor = form.observed_beam_minor.data, observed_beam_angle = form.observed_beam_angle.data, reference = form.reference.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, from_existed_id = existed)
            db.session.add(line)
            db.session.commit()
            templine = session.query(func.max(TempLine.id)).first()
            templine_id = int(templine[0])
            post = Post(templine_id=templine_id, user_email = current_user.email, time_submitted = datetime.utcnow())
            db.session.add(post)
            db.session.commit()
            flash ('Line has been added. ')
            return redirect(url_for('main.main'))
    return render_template('line_entry_form.html', title= 'Line Entry Form', form=form)


@bp.route("/line_edit_form/<llist>", methods=['GET', 'POST'])
@login_required
def line_edit_form(llist):
    llist = llist[1: len (llist) - 2]
    llist = llist.replace("'", "")
    llist = llist.split(",")
    id = llist [0]
    session = Session ()
    name = session.query(Galaxy.name).filter(Galaxy.id==id).first() 
    name = str(name)
    name = name [2: (len (name) - 3)]
    form = EditLineForm(galaxy_name = name, j_upper = llist[1], integrated_line_flux = llist[2], integrated_line_flux_uncertainty_positive = llist [3], peak_line_flux = llist[4], peak_line_flux_uncertainty_positive = llist [5], line_width = llist [6], line_width_uncertainty_positive = llist[7], observed_line_frequency = llist [8], observed_line_frequency_uncertainty_positive = llist [9], detection_type = llist[10], observed_beam_major = llist[11], observed_beam_minor = llist [12], observed_beam_angle = llist [13], reference = llist [14], notes = llist [15])
    if form.galaxy_form.data:
        return redirect(url_for('main.galaxy_entry_form'))
    if form.validate_on_submit():
        if form.submit.data:
            session = Session()
            galaxy_id = session.query(Galaxy.id).filter(Galaxy.name==form.galaxy_name.data).scalar()
            if form.freq_type.data == 'z':
                frequency, positive_uncertainty = redshift_to_frequency(form.j_upper.data, form.observed_line_frequency.data, form.observed_line_frequency_uncertainty_positive.data, form.observed_line_frequency_uncertainty_negative.data)
                negative_uncertainty = None
            else:
                frequency = form.observed_line_frequency.data
                positive_uncertainty = form.observed_line_frequency_uncertainty_positive.data
                negative_uncertainty = form.observed_line_frequency_uncertainty_negative.data
            line = EditLine(galaxy_id=galaxy_id, j_upper=form.j_upper.data, integrated_line_flux = form.integrated_line_flux.data, integrated_line_flux_uncertainty_positive = form.integrated_line_flux_uncertainty_positive.data, integrated_line_flux_uncertainty_negative = form.integrated_line_flux_uncertainty_negative.data, peak_line_flux = form.peak_line_flux.data, peak_line_flux_uncertainty_positive = form.peak_line_flux_uncertainty_positive.data, peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data, line_width=form.line_width.data, line_width_uncertainty_positive = form.line_width_uncertainty_positive.data, line_width_uncertainty_negative = form.line_width_uncertainty_negative.data, observed_line_frequency = frequency, observed_line_frequency_uncertainty_positive = positive_uncertainty, observed_line_frequency_uncertainty_negative = negative_uncertainty, detection_type = form.detection_type.data, observed_beam_major = form.observed_beam_major.data, observed_beam_minor = form.observed_beam_minor.data, observed_beam_angle = form.observed_beam_angle.data, reference = form.reference.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_edited = "Yes")
            db.session.add(line)
            db.session.commit()
            #total = update_redshift(session, galaxy_id)
            #update_redshift_error(session, galaxy_id, total)
            flash ('Line has been edited. ')
            return redirect(url_for('main.main'))
    return render_template('line_edit_form.html', title= 'Line Edit Form', form=form)

@bp.route('/galaxies')
@login_required
def galaxydic():
    session = Session()
    res1 = session.query(Galaxy)
    res2 = session.query(TempGalaxy)
    list_galaxies = [r.as_dict() for r in res1]
    list_temp_galaxies = [r.as_dict() for r in res2]
    list_galaxies.extend(list_temp_galaxies)
    return jsonify(list_galaxies)

@bp.route('/process', methods=['POST'])
@login_required
def process():
    galaxy_name = request.form['galaxy_name']
    if galaxy_name:
        return jsonify({'galaxy_name':galaxy_name})
    return jsonify({'error': 'missing data..'})

@bp.route('/galaxy/<name>')
@login_required
def galaxy(name):
    session = Session ()
    galaxy = Galaxy.query.filter_by(name=name).first_or_404()
    line = session.query(Line).filter_by(galaxy_id = galaxy.id).all()
    gdict = galaxy.__dict__
    glist = [gdict['name'], gdict['right_ascension'], gdict['declination'], gdict['coordinate_system'], gdict['lensing_flag'], gdict['classification'], gdict['notes']]
    llist = []
    for l in line:
        ldict = l.__dict__
        llist = [ldict['galaxy_id'], ldict['j_upper'], ldict['integrated_line_flux'], ldict['integrated_line_flux_uncertainty_positive'], ldict['integrated_line_flux_uncertainty_negative'], ldict['peak_line_flux'], ldict['peak_line_flux_uncertainty_positive'], ldict['peak_line_flux_uncertainty_negative'], ldict['line_width'], ldict['line_width_uncertainty_positive'], ldict['line_width_uncertainty_negative'], ldict['observed_line_frequency'], ldict['observed_line_frequency_uncertainty_positive'], ldict['observed_line_frequency_uncertainty_negative'], ldict['detection_type'], ldict['observed_beam_major'], ldict['observed_beam_minor'], ldict['observed_beam_angle'], ldict['reference'], ldict['notes']]   
    return render_template('galaxy.html', galaxy=galaxy, line = line, glist= glist, llist = llist)


@bp.route("/submit")
@login_required
def submit():
    return render_template("submit.html")

@bp.route("/convert_to_CSV/<table>/<identifier>/<symmetrical>", methods=['GET', 'POST'])
@login_required
def convert_to_CSV(table, identifier, symmetrical):
    if table == "Galaxy":
        f = open('galaxy.csv', 'w')
        out = csv.writer(f)
        out.writerow(['id', 'name', 'right_ascension', 'declination', 'coordinate_system', 'redshift', 'lensing_flag', 'classification', 'notes'])
        for item in Galaxy.query.all():
            out.writerow([item.id, item.name, item.right_ascension, item.declination, item.coordinate_system, item.redshift, item.lensing_flag, item.classification, item.notes])
        f.close()
        with open('./galaxy.csv', 'r') as file:
            galaxy_csv = file.read()
        response = make_response(galaxy_csv)
        cd = 'attachment; filename=galaxy.csv'
        response.headers['Content-Disposition'] = cd 
        response.mimetype='text/csv'
        return response
    elif table == "Line":
        f = open('line.csv', 'w')
        out = csv.writer(f)
        out.writerow(['galaxy_id', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'integrated_line_flux_uncertainty_negative', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'peak_line_flux_uncertainty_negative', 'line_width', 'line_width_uncertainty_positive', 'line_width_uncertainty_negative', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'observed_line_frequency_uncertainty_negative', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        for item in Line.query.all():
            out.writerow([item.galaxy_id, item.integrated_line_flux, item.integrated_line_flux_uncertainty_positive, item.integrated_line_flux_uncertainty_negative, item.peak_line_flux, item.peak_line_flux_uncertainty_positive, item.peak_line_flux_uncertainty_negative, item.line_width, item.line_width_uncertainty_positive, item.line_width_uncertainty_negative, item.observed_line_frequency, item.observed_line_frequency_uncertainty_positive, item.observed_line_frequency_uncertainty_negative, item.detection_type, item.observed_beam_major, item.observed_beam_minor, item.observed_beam_angle, item.reference, item.notes])
        f.close()
        with open('./line.csv', 'r') as file:
            line_csv = file.read()
        response = make_response(line_csv)
        cd = 'attachment; filename=line.csv'
        response.headers['Content-Disposition'] = cd 
        response.mimetype='text/csv'
        return response
    elif table == "Galaxy Lines":
        session = Session ()
        f = open('galaxy_lines.csv', 'w')
        out = csv.writer(f)
        galaxy_lines = session.query(Galaxy, Line).outerjoin(Galaxy).filter(Galaxy.id == identifier, Line.galaxy_id == identifier)
        out.writerow(['id', 'name', 'right_ascension', 'declination', 'coordinate_system', 'redshift', 'lensing_flag', 'classification', 'notes', 'j_upper', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'integrated_line_flux_uncertainty_negative', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'peak_line_flux_uncertainty_negative', 'line_width', 'line_width_uncertainty_positive', 'line_width_uncertainty_negative', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'observed_line_frequency_uncertainty_negative', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        for item in galaxy_lines:
            l = item [1]
            g = item [0]
            out.writerow([g.id, g.name, g.right_ascension, g.declination, g.coordinate_system, g.redshift, g.lensing_flag, g.classification, g.notes, l.j_upper, l.integrated_line_flux, l.integrated_line_flux_uncertainty_positive, l.integrated_line_flux_uncertainty_negative, l.peak_line_flux, l.peak_line_flux_uncertainty_positive, l.peak_line_flux_uncertainty_negative, l.line_width, l.line_width_uncertainty_positive, l.line_width_uncertainty_negative, l.observed_line_frequency, l.observed_line_frequency_uncertainty_positive, l.observed_line_frequency_uncertainty_negative, l.detection_type, l.observed_beam_major, l.observed_beam_minor, l.observed_beam_angle, l.reference, l.notes])
        f.close()
        with open('./galaxy_lines.csv', 'r') as file:
            galaxy_lines_csv = file.read()
        response = make_response(galaxy_lines_csv)
        cd = 'attachment; filename=galaxy_lines.csv'
        response.headers['Content-Disposition'] = cd 
        response.mimetype='text/csv'
        return response
    elif table == "Empty":
        session = Session ()
        f = open('sample.csv', 'w')
        out = csv.writer(f)
        if symmetrical == "True":
            out.writerow(['name', 'right_ascension', 'declination', 'coordinate_system', 'redshift', 'lensing_flag', 'classification', 'notes', 'j_upper', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'line_width', 'line_width_uncertainty_positive', 'freq_type', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        else:
            out.writerow(['name', 'right_ascension', 'declination', 'coordinate_system', 'redshift', 'lensing_flag', 'classification', 'notes', 'j_upper', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'integrated_line_flux_uncertainty_negative', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'peak_line_flux_uncertainty_negative', 'line_width', 'line_width_uncertainty_positive', 'freq_type', 'line_width_uncertainty_negative', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'observed_line_frequency_uncertainty_negative', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        f.close()
        with open('./sample.csv', 'r') as file:
            sample_csv = file.read()
        response = make_response(sample_csv)
        cd = 'attachment; filename=sample.csv'
        response.headers['Content-Disposition'] = cd 
        response.mimetype='text/csv'
        return response

    