from pydoc import classify_class_attrs
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
from werkzeug.urls import url_parse
import csv
from sqlalchemy import func
from config import *
from io import TextIOWrapper
from flask_security import (
    current_user,
    login_required,
    roles_required
)
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
    
    On access: Returns the form with prefilled user's data
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

@bp.route('/test', methods=['GET', 'POST'])
@roles_required('admin')
@login_required
def test():
    ''' Test route, used for development purposes only '''
    data = request.form
    # do some stuff
    return data
    #return render_template("/test.html")


@bp.route("/main", methods=['GET', 'POST'])
def main():
    '''
    Main route

    On authenticated access: returns main menu and table with galaxy data
    '''

    form = DynamicSearchForm()
    session = Session()
    if form.submit.data:
        name = form.galaxy_name.data
        galaxy = Galaxy.query.filter_by(name=name).first_or_404()
        line = session.query(Line).filter_by(galaxy_id = galaxy.id).all()
        gdict = galaxy.__dict__
        glist = [gdict['name'], gdict['right_ascension'], gdict['declination'], gdict['coordinate_system'], gdict['lensing_flag'], gdict['classification'], gdict['notes']]
        return render_template('galaxy.html', galaxy=galaxy, line = line, glist= glist)

    session = Session()
    galaxies = session.query(Galaxy).all()
    galaxies_count = session.query(Galaxy.id).count()

    count_list = []
    for i in range(galaxies_count):
        count_list.append(i)

    list_of_lines_per_species = []
    for i in range(galaxies_count):
        list_of_lines_per_species.append([])
        id = galaxies[i].id
        species = session.query(Line.species).filter(Line.galaxy_id == id).distinct().first()
        if species != None:
            for s in species:
                lines_count = session.query(Line.id).filter((Line.galaxy_id == id) & (Line.species == s)).count()
                list_of_lines_per_species[i].append((s, lines_count)) 


    lines = session.query(Line.galaxy_id, Line.species).distinct().all()

    return render_template("/main.html", galaxies=galaxies, lines=lines, list_of_lines_per_species=list_of_lines_per_species, count_list=count_list, form=form)

@bp.route('/contribute', methods=['GET'])
def contribute():

    '''
    Route with instructions on how to contribute to the database

    On authenticated access: returns an instruction page with follow-up buttons to select the method of contribution. 
    '''

    return render_template("contribute.html")


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

def check_decimal(entry):
    if re.findall(r'[0-9]\.[0-9]', entry) == []:
        return False
    else:
        return True



def within_distance(session, query, form_ra, form_dec, distance = 0, based_on_beam_angle = False, temporary = False):
    
    '''
    Takes in a point's coordinates 'form_ra' and 'form_dec' and a 'distance' to check if any galaxy from 'query' is within the 'distance'.
    Employs Great-circle distance: https://en.wikipedia.org/wiki/Great-circle_distance
    If the 'distance' is not provided, it is assumed to be 3 * Line.observed_beam_minor.
    If Line.observed_beam_minor is not available, the distance is assumed to be 5 arcsec to be in an extreme proximity. 

    Returns:
    galaxies -- a query object containing all galaxies that satisfy the distance formula (type::Query). 

    Parameters:
    session -- the session in which the \query is evoked is passed (type::Session).

    query -- predefined query object is passed containing galaxies that are to be considered in terms of their proximity 
    to some point/galaxy with given coordinates. It has to contain the Galaxy & Line table data if the distance is not passed and \based_on_beam_angle == True
    
    form_ra -- right ascension of a point/galaxy
    form_dec -- declination of a point/galaxy
    distance -- circular distance away from the point with coordinates (form_ra, form_dec). (default 0)
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
    
    #Post method
    if form_advanced.validate_on_submit():

        # Converts None entries to appropriate float and string entries 

        if form_advanced.name.data == None:
            form_advanced.name.data = ''
        if form_advanced.redshift_min.data == None:
            form_advanced.redshift_min.data = float('-inf')
        if form_advanced.redshift_max.data == None:
            form_advanced.redshift_max.data = float('inf')
        if form_advanced.lensing_flag.data == None or form_advanced.lensing_flag.data == 'Either':
            form_advanced.lensing_flag.data = ''
        if form_advanced.classification.data == None or form_advanced.classification.data == 'All':
            form_advanced.classification.data = ''
        if form_advanced.remove_classification.data == None:
            form_advanced.remove_classification.data = ''
        if form_advanced.emitted_frequency_min.data == None:
            form_advanced.emitted_frequency_min.data = float('-inf')
        if form_advanced.emitted_frequency_max.data == None:
            form_advanced.emitted_frequency_max.data = float('inf')
        
        if form_advanced.species.data == None or form_advanced.species.data == 'Any':
            form_advanced.species.data = ''   

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

        buffer = []
        index = 0
        is_all = False
        for c in form_advanced.classification.data:
            if c == "All":
                is_all = True
            else:
                buffer.append(c)
                index = index + 1
        
        for i in range (index, 12):
            if is_all:
                buffer.append("(")
            else:
                buffer.append("asyunujnjnghfawek")
        
        # Query displaying galaxies based on the data from form_advanced
        if form_advanced.galaxySearch.data:
            
            # Additional filter if radius is specified
            if (form_advanced.right_ascension_point.data != None) and (form_advanced.declination_point.data != None) and ((form_advanced.radius_d.data != None) or (form_advanced.radius_m.data != None) or (form_advanced.radius_s.data != None)):
                distance=math.radians(to_zero(form_advanced.radius_d.data)+to_zero(form_advanced.radius_m.data)/60+to_zero(form_advanced.radius_s.data)/3600) 
                galaxies=session.query(Galaxy, Line).outerjoin(Line)
                galaxies = within_distance(session, galaxies, form_advanced.right_ascension_point.data, form_advanced.declination_point.data, distance=distance)
                
            else:
                galaxies=session.query(Galaxy, Line).outerjoin(Line)
            # quick workaround since sqlalchemy does not take two strings equal to each other
            l_flag = Galaxy.lensing_flag + Galaxy.lensing_flag
            l_data = form_advanced.lensing_flag.data + form_advanced.lensing_flag.data
            # Filters in respect to galaxy parameters
            galaxies=galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)), ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (Galaxy.declination.between(dec_to_float(to_m_inf(form_advanced.declination_min.data)), dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data) | (Galaxy.redshift == None)) & (l_flag.contains(l_data) | (Galaxy.lensing_flag == None)))
            galaxies=galaxies.filter(Galaxy.classification.contains(buffer[0]) | Galaxy.classification.contains(buffer[1]) | Galaxy.classification.contains(buffer[2]) | Galaxy.classification.contains(buffer[3]) | Galaxy.classification.contains(buffer[4]) | Galaxy.classification.contains(buffer[5]) | Galaxy.classification.contains(buffer[6]) | Galaxy.classification.contains(buffer[7]) | Galaxy.classification.contains(buffer[8]) | Galaxy.classification.contains(buffer[9]) | Galaxy.classification.contains(buffer[10]) | Galaxy.classification.contains(buffer[11]) | (Galaxy.classification == None))

            galaxies=galaxies.filter(~Galaxy.classification.contains(form_advanced.remove_classification.data))

            galaxies = galaxies.filter((Line.id == None) | ((Line.emitted_frequency.between(form_advanced.emitted_frequency_min.data, form_advanced.emitted_frequency_max.data) | (Line.emitted_frequency == None )) & ((Line.species.contains(form_advanced.species.data)) | (Line.species == None)) & (Line.integrated_line_flux.between(form_advanced.integrated_line_flux_min.data, form_advanced.integrated_line_flux_max.data) | (Line.integrated_line_flux == None)) & (Line.peak_line_flux.between(form_advanced.peak_line_flux_min.data, form_advanced.peak_line_flux_max.data) | (Line.peak_line_flux == None)) & (Line.line_width.between(form_advanced.line_width_min.data, form_advanced.line_width_max.data) | (Line.line_width == None )) & (Line.observed_line_frequency.between(form_advanced.observed_line_frequency_min.data, form_advanced.observed_line_frequency_max.data) | (Line.observed_line_frequency == None )) & (Line.observed_beam_major.between(form_advanced.observed_beam_major_min.data, form_advanced.observed_beam_major_max.data) | (Line.observed_beam_major == None )) & (Line.observed_beam_minor.between(form_advanced.observed_beam_minor_min.data, form_advanced.observed_beam_minor_max.data) | (Line.observed_beam_minor == None )) & (Line.reference.contains(form_advanced.reference.data) | (Line.reference == None)) & (Line.detection_type.contains(form_advanced.detection_type.data) | (Line.detection_type == None))  ))

            galaxies = galaxies.distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()

            return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)   

        # Query displaying lines based on the data from form_advanced    
        elif form_advanced.lineSearch.data:
            if (form_advanced.right_ascension_point.data != None) and (form_advanced.declination_point.data != None) and ((form_advanced.radius_d.data != None) or (form_advanced.radius_m.data != None) or (form_advanced.radius_s.data != None)):
                distance=math.radians(to_zero(form_advanced.radius_d.data)+to_zero(form_advanced.radius_m.data)/60+to_zero(form_advanced.radius_s.data)/3600) 
                galaxies=session.query(Galaxy, Line).outerjoin(Galaxy)
                galaxies = within_distance(session, galaxies, form_advanced.right_ascension_point.data, form_advanced.declination_point.data, distance=distance)
                
            else:
                galaxies=session.query(Galaxy, Line).outerjoin(Galaxy)


            galaxies=galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)), ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (Galaxy.declination.between(dec_to_float(to_m_inf(form_advanced.declination_min.data)), dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data) | (Galaxy.redshift == None) ) & (Galaxy.lensing_flag.contains(form_advanced.lensing_flag.data) | (Galaxy.lensing_flag == None)) & (Galaxy.classification.contains(form_advanced.classification.data) | (Galaxy.classification == None)))

            galaxies=galaxies.filter((Line.emitted_frequency.between(form_advanced.emitted_frequency_min.data, form_advanced.emitted_frequency_max.data) | (Line.emitted_frequency == None )) & ((Line.species.contains(form_advanced.species.data)) | (Line.species == None)) & (Line.integrated_line_flux.between(form_advanced.integrated_line_flux_min.data, form_advanced.integrated_line_flux_max.data) | (Line.integrated_line_flux == None)) & (Line.peak_line_flux.between(form_advanced.peak_line_flux_min.data, form_advanced.peak_line_flux_max.data) | (Line.peak_line_flux == None)) & (Line.line_width.between(form_advanced.line_width_min.data, form_advanced.line_width_max.data) | (Line.line_width == None )) & (Line.observed_line_frequency.between(form_advanced.observed_line_frequency_min.data, form_advanced.observed_line_frequency_max.data) | (Line.observed_line_frequency == None )) & (Line.observed_beam_major.between(form_advanced.observed_beam_major_min.data, form_advanced.observed_beam_major_max.data) | (Line.observed_beam_major == None )) & (Line.observed_beam_minor.between(form_advanced.observed_beam_minor_min.data, form_advanced.observed_beam_minor_max.data) | (Line.observed_beam_minor == None )) & (Line.reference.contains(form_advanced.reference.data) | (Line.reference == None)) )
            
            galaxies=galaxies.order_by(Galaxy.name).all()

            return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)

        # Is not called
        else:
            galaxies = session.query(Galaxy, Line).outerjoin(Line).distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()
        return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)
    
    # Get method
    else:
        galaxies = session.query(Galaxy, Line).outerjoin(Line).distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()
    
    return render_template("/query_results.html", form=form, form_advanced=form_advanced, galaxies=galaxies)



def test_frequency (input_frequency_str, species_type):

    '''
    Given frequency and species type, determines the family and returns the result of the corresponding call on test_frequency_for_family.

    Returns:
    dict_frequency -- The corresponding frequency from our dictionary if found (type::float), False otherwise (type::bool). 
    message -- Error message if several possible corresponding values are found in our dictionary (type::string).

    Parameters:
    intput_frequency_str -- Frequency input submitted by user (type::string).
    species_type -- Species type of the corresponding line entry submitted by user (type::string).
    '''
    
    family = False

    if species_type in CO:
        family = CarbonMonoxide
        species_type = CO[species_type]
    elif species_type in THIRTEEN_CO:
        family = CarbonMonoxide
        species_type = THIRTEEN_CO[species_type]
    elif species_type in C17O:
        family = CarbonMonoxide
        species_type = C17O[species_type]
    elif species_type in C18O:
        family = CarbonMonoxide
        species_type = C18O[species_type]
    elif species_type in CF:
        family = Fluoromethylidyne_Fluoromethyliumylidene
        species_type = CF[species_type]
    elif species_type in CF_PLUS:
        family = Fluoromethylidyne_Fluoromethyliumylidene
        species_type = CF_PLUS[species_type]
    elif species_type in CCH:
        family = Ethynyl_Methylidynium_Mathylidyne
        species_type = CCH[species_type]
    elif species_type in CH_PLUS:
        family = Ethynyl_Methylidynium_Mathylidyne
        species_type = CH_PLUS[species_type]
    elif species_type in CH2_P1_SLASH_2:
        family = Ethynyl_Methylidynium_Mathylidyne
        species_type = CH2_P1_SLASH_2[species_type]
    elif species_type in CH2_P3_SLASH_2:
        family = Ethynyl_Methylidynium_Mathylidyne
        species_type = CH2_P3_SLASH_2[species_type]
    elif species_type in CI_BRACKET_C_HYPHEN_atom_BRACKET:
        family = AtomicCarbon_IonisedCarbon
        species_type = CI_BRACKET_C_HYPHEN_atom_BRACKET[species_type]
    elif species_type in CII:
        family = AtomicCarbon_IonisedCarbon
        species_type = CII[species_type]
    elif species_type in CN_MINUS:
        family = CyanideAnion_CyanideRadical
        species_type = CN_MINUS[species_type]
    elif species_type in CN:
        family = CyanideAnion_CyanideRadical
        species_type = CN[species_type]
    elif species_type in CS:
        family = CarbonMonosulfide
        species_type = CS[species_type]
    elif species_type in Ha:
        family = HydrogenRecombinationLine
        species_type = Ha[species_type]
    elif species_type in H2O:
        family = Water_orthoOxidaniumyl_paraOxidaniumyl
        species_type = H2O[species_type]
    elif species_type in o_HYPHEN_H2O_PLUS:
        family = Water_orthoOxidaniumyl_paraOxidaniumyl
        species_type = o_HYPHEN_H2O_PLUS[species_type]
    elif species_type in p_HYPHEN_H2O_PLUS:
        family = Water_orthoOxidaniumyl_paraOxidaniumyl
        species_type = p_HYPHEN_H2O_PLUS[species_type]
    elif species_type in HCN:
        family = HydrogenCyanide_HydrogenIsocyanide
        species_type = HCN[species_type]
    elif species_type in HNC:
        family = HydrogenCyanide_HydrogenIsocyanide
        species_type = HNC[species_type]
    elif species_type in HCO_PLUS:
        family = Formylium
        species_type = HCO_PLUS[species_type]
    elif species_type in HF:
        family = HydrogenFluoride
        species_type = HF[species_type]
    elif species_type in LiH:
        family = LithiumHydride
        species_type = LiH[species_type]
    elif species_type in N2H_PLUS:
        family = Diazenylium
        species_type = N2H_PLUS[species_type]
    elif species_type in NH3:
        family = Ammonia
        species_type = NH3[species_type]
    elif species_type in NII_BRACKET_N_PLUS_HYPHEN_atom_BRACKET:
        family = AtomicNitrogen
        species_type = NII_BRACKET_N_PLUS_HYPHEN_atom_BRACKET[species_type]
    elif species_type in NO:
        family = NitricOxide_NitricOxideIon
        species_type = NO[species_type]
    elif species_type in NO_PLUS:
        family = NitricOxide_NitricOxideIon
        species_type = NO_PLUS[species_type]
    elif species_type in OI:
        family = Oxygen_IonisedOxygen
        species_type = OI[species_type]
    elif species_type in OIII:
        family = Oxygen_IonisedOxygen
        species_type = OIII[species_type]
    elif species_type in OH_PLUS:
        family = Hydroxyl
        species_type = OH_PLUS[species_type]
    elif species_type in OH:
        family = Hydroxyl
        species_type = OH[species_type]
    elif species_type in PN:
        family = PhosphorousNitride
        species_type = PN[species_type]
    elif species_type in SiC:
        family = SiliconMonocarbide 
        species_type = SiC[species_type]
    elif species_type in SiN:
        family = SiliconMononitride
        species_type = SiN[species_type]
    elif species_type in SiO:
        family = SiliconMonoxide
        species_type = SiO[species_type]
    elif species_type in SO2:
        family = SulfurDioxide
        species_type = SO2[species_type]

    if family == False:
        dict_frequency = False
        message = " Species name could not be identified."
    else:
        dict_frequency, message = test_frequency_for_family(family, species_type, input_frequency_str)
    
    return dict_frequency, message


def test_frequency_for_family(family, species_type, input_frequency_str):

    '''
    Given frequency, family, and species type, returns the corresponding unique frequncy from our dictionary if found, or False with the corresponding 
    error message if result is not unique.

    Returns:
    dict_frequency -- The corresponding frequency from our dictionary if found (type::float), False otherwise (type::bool). 
    message -- Error message if several possible corresponding values are found in our dictionary (type::string).

    Parameters:
    family -- Dictionary of dictionaries of species types and their corresponding quantum numbers.
    intput_frequency_str -- Frequency input submitted by user (type::string).
    species_type -- Species type of the corresponding line entry submitted by user (type::string).
    '''
    
    nearest_frequency = 0
    message = ''
    input_frequency = float(input_frequency_str)

    # Iterates over family members not specified by the user
    for species_name, species_dict in family.items():
    
        if species_name != species_type:


            if input_frequency in species_dict:
                message = message + "We found the exact same rest frequency for ({}) species. Did you mean ({}) instead of ({})? ".format(species_name, species_name, species_type) 
            else: 
                delta = input_frequency
                for key, value in species_dict.items():
                    if abs(key-input_frequency) < delta:
                        delta = abs(key-input_frequency)
                        nearest_frequency = key
                
                if check_decimal(input_frequency_str):
                    decimals = input_frequency_str[input_frequency_str.find('.')+1:]
                    precision = len(decimals)
                    range_1 = input_frequency - (0.1) ** precision 
                    range_2 = input_frequency + (0.1) ** precision 
                else:
                    precision = len(input_frequency_str)
                    for c in input_frequency_str:
                        if c != '0':
                            precision -= 1
                        else:
                            pass
                    range_1 = input_frequency - (10) ** precision 
                    range_2 = input_frequency + (10) ** precision

                # Check if there are any values of similar species in the range
                for key, value in species_dict.items():
                    if key > (range_1) and (key < range_2):
                        message_1 = "Species ({}) has a transition ({}) at a rest frequency of ({}) GHz. ".format(species_name, value, key)
                        message = message + message_1

        else:
            pass

    # Finds the specified by user species 
    # and returns the frequency from dictionary if no previous errors returned.
    for species_name, species_dict in family.items():

        if species_name == species_type:

            if input_frequency in species_dict:
                dict_frequency = input_frequency
            else: 
                delta = input_frequency
                for key, value in species_dict.items():
                    if abs(key-input_frequency) < delta:
                        delta = abs(key-input_frequency)
                        nearest_frequency = key
                
                if check_decimal(input_frequency_str):
                    decimals = input_frequency_str[input_frequency_str.find('.')+1:]
                    precision = len(decimals)
                    range_1 = input_frequency - (0.1) ** precision 
                    range_2 = input_frequency + (0.1) ** precision 
                else:
                    precision = len(input_frequency_str)
                    for c in input_frequency_str:
                        if c != '0':
                            precision -= 1
                        else:
                            pass
                    range_1 = input_frequency - (10) ** precision 
                    range_2 = input_frequency + (10) ** precision

                # Check if there are more than one value in the range
                count_values_in_range = 0
                for key, value in species_dict.items():
                    if key > (range_1) and (key < range_2):
                        count_values_in_range += 1
                        if (count_values_in_range > 1) or (message != ''):
                            message_1 = "Species ({}) has a transition ({}) at a rest frequency of ({}) GHz. ".format(species_name, value, key)
                            message = message + message_1

                dict_frequency = nearest_frequency
            
        else:
            pass

    
    if message == '':
        return dict_frequency, message

    else:
        message = ": Multiple possible lines identified within the submitted frequency precision. Please double check the species name and/or add additional digits of precision to the frequency, then resubmit. Possible matches: \n" + message

        return False, message  

def update_right_ascension(galaxy_id):
    session = Session()
    lines = session.query(Line.right_ascension).filter(Line.galaxy_id==galaxy_id).all()
    total = 0
    count = 0
    for line in lines:
        total += line
        count += 1
    if count != 0:
        right_ascension = total / count
        return right_ascension
    else: 
        return False
    
def update_declination(galaxy_id):
    session = Session()
    lines = session.query(Line.declination).filter(Line.galaxy_id==galaxy_id).all()
    total = 0
    count = 0
    for line in lines:
        total += line
        count += 1
    if count != 0:
        declination = total / count
        return declination
    else: 
        return False


@bp.route("/entry_file", methods=['GET', 'POST'])
@login_required
def entry_file():

    '''
    Submit CSV route

    For a given CSV:
    First parses all entries checking if values are within the requirements and according to the format. 
    If not, a separate error message for each error is displayed. Otherwise, entries are being submitted.
    '''

    form = UploadFileForm()
    if request.method == 'POST':
        csvfile = request.files['file']
        csv_file = TextIOWrapper(csvfile, encoding='utf-8-sig', errors = 'ignore')
        reader = csv.DictReader(x.replace('\0', '') for x in csv_file)
        data = [row for row in reader]
        classification_options = {"LBG": "LBG (Lyman Break Galaxy)", "MS": "MS (Main Sequence Galaxy)", "SMB": "SMB (Submillimeter Galaxy)", "DSFG": "DSFG (Dusty Star-Forming Galaxy)", "SB": "SB (Starburst)", "AGN": "AGN (Contains a Known Active Galactic Nucleus)", "QSO": "QSO (Optically Bright AGN)", "Quasar": "Quasar (Optical and Radio Bright AGN)", "RQ-AGN": "RQ-AGN (Radio-Quiet AGN)", "RL-AGN": "RL-AGN (Radio-Loud AGN)", "RG": "RG (Radio Galaxy)", "BZK": "BZK (BZK-Selected Galaxy)"}

        if data == []:
            flash ("CSV File is empty. ")
        else:
            validated = True
            row_count = 0   
            keys = COL_NAMES.keys()
            key_list = list(keys)    
            missing_column = []
            for k in key_list:
                if k not in data[0]:
                    validated = False
                    missing_column.append(k)

            if not validated:
                flash ("Incorrect column names - please check sample file")     
                flash(" Missing Column/s : " + str(missing_column))
            for row in data:
                row_count += 1
                is_empty = True
                for element in row:
                    if row[element]:
                        is_empty = False
                if not is_empty:
                    if row == []:
                        flash ("Entry " + str(row_count) + ' was an empty row')
                    
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
                        row_integrated_line_flux_uncertainty_positive = row[COL_NAMES['integrated_line_flux_uncertainty_positive']].strip()
                        row_integrated_line_flux_uncertainty_negative = row[COL_NAMES['integrated_line_flux_uncertainty_negative']].strip()
                        row_peak_line_flux = row[COL_NAMES['peak_line_flux']].strip()
                        row_peak_line_flux_uncertainty_positive = row[COL_NAMES['peak_line_flux_uncertainty_positive']].strip()
                        row_peak_line_flux_uncertainty_negative = row[COL_NAMES['peak_line_flux_uncertainty_negative']].strip()
                        row_line_width = row[COL_NAMES['line_width']].strip()
                        row_line_width_uncertainty_positive = row[COL_NAMES['line_width_uncertainty_positive']].strip()
                        row_line_width_uncertainty_negative = row[COL_NAMES['line_width_uncertainty_negative']].strip()
                        row_freq_type = row[COL_NAMES['freq_type']].strip()
                        row_observed_line_frequency = row[COL_NAMES['observed_line_frequency']].strip()
                        row_observed_line_frequency_uncertainty_positive = row[COL_NAMES['observed_line_frequency_uncertainty_positive']].strip()
                        row_observed_line_frequency_uncertainty_negative = row[COL_NAMES['observed_line_frequency_uncertainty_negative']].strip()
                        row_detection_type = row[COL_NAMES['detection_type']].strip()
                        row_observed_beam_major = row[COL_NAMES['observed_beam_major']].strip()
                        row_observed_beam_minor = row[COL_NAMES['observed_beam_minor']].strip()
                        row_observed_beam_angle = row[COL_NAMES['observed_beam_angle']].strip()
                        row_reference = row[COL_NAMES['reference']].strip()
                        row_notes = row[COL_NAMES['l_notes']].strip()

                        # Check whether the values pass the conditions
                        if row_name == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Galaxy Name is Mandatory")
                        if row_coordinate_system != "ICRS" and row_coordinate_system != "J2000":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Coordinate System can be ICRS or J2000 only.")
                        if row_lensing_flag != "Lensed" and row_lensing_flag != "Unlensed" and row_lensing_flag != "":
                            if row_lensing_flag != "L" and row_lensing_flag != "U" and row_lensing_flag != "l" and row_lensing_flag != "u":
                                validated = False
                                flash ("Entry " + str(row_count) + ": Please enter either \"Lensed\", \"Unlensed\" or \"L\", \"U\" under {}.".format(row_lensing_flag))
                            else:
                                if row_lensing_flag == "U" or row_lensing_flag == "u":
                                    row_lensing_flag = "Unlensed"
                                else: row_lensing_flag = "Lensed"
                        if entered_classification == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Classification is Mandatory")
                        row_classification = ""
                        for key, value in classification_options.items():
                            if key.upper() in entered_classification.upper():
                                row_classification = row_classification + ", " + value
                        row_classification = row_classification [2:]
                        if row_classification == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Please enter Correction Classifications")
                        if row_right_ascension == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Right Ascension is Mandatory")
                        if re.search(ra_reg_exp, row_right_ascension) == None:
                            validated = False
                            flash ("Entry " + str(row_count) + ": Enter Right Ascension in a proper format")
                        if row_declination == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Declination is Mandatory")
                        if re.search(dec_reg_exp, row_declination) == None:
                            validated = False
                            flash ("Entry " + str(row_count) + ": Enter Declination in a proper format")
                        if row_emitted_frequency == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Emitted Frequency is Mandatory")
                        try:
                            dict_frequency, message = test_frequency(row_emitted_frequency, row_species)
                            if dict_frequency == False:
                                flash("Entry " + str(row_count) + message)
                                validated = False
                        except:
                            pass
                        if row_species == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Please specify species")
                        if row_integrated_line_flux == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Integrated Line Flux is Mandatory")
                        if row_integrated_line_flux_uncertainty_positive == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Integrated Line Flux Positive Uncertainty is Mandatory")
                        if row_integrated_line_flux_uncertainty_negative == "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Integrated Line Flux Negative Uncertainty is Mandatory")
                        if row_integrated_line_flux_uncertainty_positive != "":
                            try:
                                if float (row_integrated_line_flux_uncertainty_positive) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Integrated Line Flux Positive Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_integrated_line_flux_uncertainty_negative != "":
                            try:
                                if float (row_integrated_line_flux_uncertainty_negative) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Integrated Line Flux Negative Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_peak_line_flux_uncertainty_positive != "":
                            try:
                                if float (row_peak_line_flux_uncertainty_positive) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Peak Line Flux Positive Uncertainty must be greater than 0")
                            except:
                                pass                
                        if row_peak_line_flux_uncertainty_negative != "":
                            try:
                                if float (row_peak_line_flux_uncertainty_negative) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Peak Line Flux Negative Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_line_width_uncertainty_positive != "":
                            try:
                                if float (row_line_width_uncertainty_positive) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Line Width Positive Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_line_width_uncertainty_negative != "":
                            try:
                                if float (row_line_width_uncertainty_negative) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Line Width Negative Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_freq_type != "z" and row_freq_type != "f" and row_freq_type != "":
                            validated = False
                            flash ("Entry " + str(row_count) + ": Please enter either \"z\", \"f\" under {}.".format(row_freq_type))
                        if row_observed_line_frequency_uncertainty_positive != "":
                            try:
                                if float (row_observed_line_frequency_uncertainty_positive) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Observed Line Frequency Positive Uncertainty must be greater than 0")
                            except:
                                pass
                        if row_observed_line_frequency_uncertainty_negative != "":
                            try:
                                if float (row_observed_line_frequency_uncertainty_negative) < 0:
                                    validated = False
                                    flash ("Entry " + str(row_count) + ": Observed Line Frequency Negative Uncertainty must be greater than 0")
                            except:
                                pass
            
        # If passed all conditions
        if validated:
            flash ("All entered values have been validated")
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
                        row_classification = row_classification + ", " + value
                row_classification = row_classification [2:]
                row_emitted_frequency = row[COL_NAMES['emitted_frequency']].strip()
                row_species = row[COL_NAMES['species']].strip()
                row_integrated_line_flux = row[COL_NAMES['integrated_line_flux']].strip()
                row_integrated_line_flux_uncertainty_positive = row[COL_NAMES['integrated_line_flux_uncertainty_positive']].strip()
                row_integrated_line_flux_uncertainty_negative = row[COL_NAMES['integrated_line_flux_uncertainty_negative']].strip()
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
                row_observed_line_frequency = row[COL_NAMES['observed_line_frequency']].strip()
                row_observed_line_frequency_uncertainty_positive = row[COL_NAMES['observed_line_frequency_uncertainty_positive']].strip()
                row_observed_line_frequency_uncertainty_negative = row[COL_NAMES['observed_line_frequency_uncertainty_negative']].strip()
                if row_observed_line_frequency_uncertainty_negative == "":
                    row_observed_line_frequency_uncertainty_negative = row_observed_line_frequency_uncertainty_positive
                row_detection_type = row[COL_NAMES['detection_type']].strip()
                row_observed_beam_major = row[COL_NAMES['observed_beam_major']].strip()
                row_observed_beam_minor = row[COL_NAMES['observed_beam_minor']].strip()
                row_observed_beam_angle = row[COL_NAMES['observed_beam_angle']].strip()
                row_reference = row[COL_NAMES['reference']].strip()
                row_notes = row[COL_NAMES['l_notes']].strip()


                ra = ra_to_float(row_right_ascension)
                dec = dec_to_float(row_declination)

                # Check whether this galaxy entry has been previously uploaded and/or approved
                session = Session()
                galaxies=session.query(Galaxy, Line).outerjoin(Line).filter(Galaxy.name == row_name)
                galaxies = within_distance(session, galaxies, ra, dec, based_on_beam_angle=True)
                galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)

                tempgalaxies=session.query(TempGalaxy).filter(TempGalaxy.name == row_name)
                tempgalaxies=within_distance(session, tempgalaxies, ra, dec, based_on_beam_angle=True, temporary=True)

                similar_galaxy = galaxies.first()
                similar_tempgalaxy = tempgalaxies.first()

                
                # If this galaxy entry has not been previously uploaded and/or approved, then upload. 
                if (similar_tempgalaxy == None) & (similar_galaxy == None):

                    galaxy = TempGalaxy(name = row_name,
                                        right_ascension = ra,
                                        declination = dec,
                                        coordinate_system = row_coordinate_system,
                                        lensing_flag = row_lensing_flag,
                                        classification = row_classification,
                                        notes = row_g_notes,
                                        user_submitted = current_user.username,
                                        user_email = current_user.email,
                                        time_submitted = datetime.utcnow())
                    db.session.add(galaxy)
                    new_id = db.session.query(func.max(TempGalaxy.id)).first()
                    id = new_id [0]
                    from_existed = None
                    tempgalaxy = db.session.query(func.max(TempGalaxy.id)).first()
                    tempgalaxy_id = int(tempgalaxy[0])
                    post = Post(tempgalaxy_id=tempgalaxy_id, user_email = current_user.email, time_submitted = datetime.utcnow())
                    db.session.add(post)
                    db.session.commit()
                # If this galaxy has been previously uploaded but not yet approved / deleted, then remember id to assign the corresponding line submission. 
                elif (similar_tempgalaxy != None) & (similar_galaxy == None):
                    id = similar_tempgalaxy.id
                    from_existed = None
                # If this galaxy has been previously approved and is stored in db, then remember id to assign the correspondin line submissions. 
                else:
                    id = similar_galaxy[0].id
                    from_existed = id

                dict_frequency, message = test_frequency(row_emitted_frequency, row_species)


                # If observed frequency submitted as redshift, convert to frequency.
                if row_freq_type == "z":
                    frequency, positive_uncertainty = redshift_to_frequency(dict_frequency, to_none( row_observed_line_frequency), to_none( row_line_width_uncertainty_positive), to_none( row_line_width_uncertainty_negative))
                    negative_uncertainty = None
                else:
                    frequency = to_none( row_observed_line_frequency)
                    positive_uncertainty = to_none( row_line_width_uncertainty_positive)
                    negative_uncertainty = to_none( row_line_width_uncertainty_negative)

                # Check whether this line entry has been previously uploaded and/or approved
                check_same_temp_line = db.session.query(TempLine.id).filter((TempLine.emitted_frequency == dict_frequency) & (TempLine.observed_line_frequency == frequency) & (TempLine.galaxy_name == row_name) & (TempLine.species == row_species) & (TempLine.integrated_line_flux == to_none(row_integrated_line_flux)) & (TempLine.integrated_line_flux_uncertainty_positive == to_none(row_integrated_line_flux_uncertainty_positive))).first()

                galaxy_id = db.session.query(Galaxy.id).filter_by(name=row_name).scalar()

                check_same_line = db.session.query(Line.id).filter((Line.galaxy_id == galaxy_id) & (Line.emitted_frequency == dict_frequency) & (Line.observed_line_frequency == frequency) & (Line.integrated_line_flux == to_none(row_integrated_line_flux)) & (Line.integrated_line_flux_uncertainty_positive == to_none(row_integrated_line_flux_uncertainty_positive)) & (Line.species == row_species)).first()

                # If this galaxy entry has not been previously uploaded and/or approved, then upload. 
                if (check_same_temp_line == None) & (check_same_line == None):

                    line = TempLine (galaxy_id = id,
                                    from_existed_id = from_existed,
                                    emitted_frequency = dict_frequency, 
                                    species = row_species,  
                                    integrated_line_flux =to_none( row_integrated_line_flux), 
                                    integrated_line_flux_uncertainty_positive =to_none( row_integrated_line_flux_uncertainty_positive), 
                                    integrated_line_flux_uncertainty_negative =to_none( row_integrated_line_flux_uncertainty_negative), 
                                    peak_line_flux =to_none(row_peak_line_flux),
                                    peak_line_flux_uncertainty_positive =to_none( row_peak_line_flux_uncertainty_positive),
                                    peak_line_flux_uncertainty_negative=to_none( row_peak_line_flux_uncertainty_negative), 
                                    line_width=to_none( row_line_width),
                                    line_width_uncertainty_positive =to_none( row_line_width_uncertainty_positive),
                                    line_width_uncertainty_negative =to_none( row_line_width_uncertainty_negative),
                                    observed_line_frequency =frequency,
                                    observed_line_frequency_uncertainty_positive =positive_uncertainty,
                                    observed_line_frequency_uncertainty_negative =negative_uncertainty,
                                    detection_type = row_detection_type,
                                    observed_beam_major =to_none( row_observed_beam_major), 
                                    observed_beam_minor =to_none( row_observed_beam_minor),
                                    observed_beam_angle =to_none( row_observed_beam_angle),
                                    reference = row_reference,
                                    notes = row_notes,
                                    user_submitted = current_user.username,
                                    user_email = current_user.email,
                                    time_submitted = datetime.utcnow(),
                                    galaxy_name = row_name,
                                    right_ascension = ra,
                                    declination = dec
                                    )                
                    db.session.add(line)

                    try:
                        db.session.commit()
                        templine = db.session.query(func.max(TempLine.id)).first()
                        templine_id = int(templine[0])
                        post = Post(templine_id=templine_id, user_email = current_user.email, time_submitted = datetime.utcnow())
                        db.session.add(post)
                        db.session.commit()
                        #flash ("Entry number {} has been successfully uploaded.".format(row_count))
                    except:
                        db.session.rollback()
                        raise

                else:
                    # If this line entry already exists in db, pass.
                    pass

            flash('Entries have been successfully uploaded')
        else:
            flash('File not uploaded. Please resubmit the file once corrected.')

    return render_template ("/entry_file.html", title = "Upload File", form = form)


def ra_to_float(coordinates):

    '''
    Given right ascension value as either a string representing a float number or a string of the 00h00m00s format,
    return the corresponding float value.

    Returns:
    coordinates -- float value of right ascension (type::float).

    Parameters:
    coordinates -- a string representing a float or 00h00m00s format right ascension.
    '''

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
        
    '''
    Given declination value as either a string representing a float number or a string of the +/-00d00m00s format,
    return the corresponding float value.

    Returns:
    coordinates -- float value of declination (type::float).

    Parameters:
    coordinates -- a string representing a float or +/-00d00m00s format declination.
    '''
    
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

def ra_to_string(ra_float):
    '''
    Analogue to JS function in coordinates.js
    '''
    ra_string = ""
    h = round(ra_float//15)
    m = round((ra_float - h*15) // 0.25)
    s = round(((ra_float - h*15) - m*0.25) * 240, 3) 
    if h < 10:
        h = "0"+str(h)+"h"
    else:
        h = str(h)+"h"
    if m < 10:
        m = "0"+str(m)+"m"
    else:
        m = str(m)+"m"
    if s < 10:
        s = "0"+str(s)+"s"
    else:
        s = str(s)+"s"
    ra_string = h+m+s
    return ra_string
    

def dec_to_string(dec_float):
    pass

@bp.route("/galaxy_entry_form", methods=['GET', 'POST'])
@login_required
def galaxy_entry_form():

    '''
    Galaxy entry form route

    On access: Returns a form to submit a galaxy entry.
    On submit: If the values areunappropriate, an error is returned. 
    If the entry seems to exist already in the database or if its coordinates closely resemble the coordinates of an existing galaxy,
    then a clarification is returned with the list of the galaxies that the User could potentially mean. 
    Otherwise, the entry is uploaded. 
    '''

    form = AddGalaxyForm()
    session=Session()
    if form.validate_on_submit ():

        if form.submit.data:
            try:
                DEC = dec_to_float(form.declination.data)
            except:
                DEC = form.declination.data
            try:
                RA = ra_to_float(form.right_ascension.data)
            except:
                RA = form.right_ascension.data 


            # Check whether this galaxy entry has been previously uploaded and/or approved
            galaxies=session.query(Galaxy, Line).outerjoin(Line)
            galaxies = within_distance(session, galaxies, RA, DEC, based_on_beam_angle=True)
            galaxies = galaxies.group_by(Galaxy.name).order_by(Galaxy.name)

            tempgalaxies=session.query(TempGalaxy)
            tempgalaxies=within_distance(session, tempgalaxies, RA, DEC, based_on_beam_angle=True, temporary=True)

            similar_galaxy = galaxies.first()
            similar_tempgalaxy = tempgalaxies.first()

            if (similar_galaxy != None) or (similar_tempgalaxy != None):
                if similar_galaxy != None:
                    another_exists = True
                else:
                    another_exists = False
                if similar_tempgalaxy != None:
                    same_temp_exists = True
                else:
                    same_temp_exists = False
                return render_template('galaxy_entry_form.html', title= 'Galaxy Entry Form', form=form, galaxies=galaxies, same_temp_exists=same_temp_exists, another_exists=another_exists)
            classifications = ' '.join([elem + ", " for elem in form.classification.data])[:-2]
            galaxy = TempGalaxy(name=form.name.data, right_ascension=RA, declination = DEC, coordinate_system = form.coordinate_system.data, classification = classifications, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_similar = None, time_submitted = datetime.utcnow())
            db.session.add(galaxy)
            db.session.commit()
            tempgalaxy = db.session.query(func.max(TempGalaxy.id)).first()
            tempgalaxy_id = int(tempgalaxy[0])
            post = Post(tempgalaxy_id=tempgalaxy_id, user_email = current_user.email, time_submitted = datetime.utcnow())
            db.session.add(post)
            db.session.commit()
            flash ('Galaxy has been added. ')

        # If User still wants to submit the entry even though similar exist.
        if form.submit_anyway.data:
            try:
                DEC = dec_to_float(form.declination.data)
            except:
                DEC = form.declination.data
            try:
                RA = ra_to_float(form.right_ascension.data)
            except:
                RA = form.right_ascension.data 

            galaxy = TempGalaxy(name=form.name.data, right_ascension=RA, declination = DEC, coordinate_system = form.coordinate_system.data, classification = form.classification.data, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, time_submitted = datetime.utcnow())
            db.session.add(galaxy)
            db.session.commit()
            tempgalaxy = db.session.query(func.max(TempGalaxy.id)).first()
            tempgalaxy_id = int(tempgalaxy[0])
            post = Post(tempgalaxy_id=tempgalaxy_id, user_email = current_user.email, time_submitted = datetime.utcnow())
            db.session.add(post)
            db.session.commit()
            flash ('Galaxy has been added. ')

        # If User preferred not to submit the entry. 
        if form.do_not_submit.data:
            return redirect (url_for ('main.main'))

        # If User wants to add a line entry to just submitted galaxy entry. 
        if form.new_line.data:
            return redirect(url_for('main.line_entry_form'))
    return render_template('galaxy_entry_form.html', title= 'Galaxy Entry Form', form=form)

@bp.route("/galaxy_edit_form/<id>", methods=['GET', 'POST'])
@login_required
def galaxy_edit_form(id):

    '''
    Galaxy edit route
    On access: Prefills the form with the desired galaxy to be edited.
    On submit: Submits the edits. An error is raised if unappropriated values are entered. 
    '''

    session=Session()
    galaxy = session.query(Galaxy).filter(Galaxy.id == id).first()
    classifications = ' '.join([str(elem) + "," for elem in galaxy.classification.split(', ')])[:-1]
    classlist = galaxy.classification.split(', ')
    for c in classlist:
        c = c[1:]
    form = EditGalaxyForm(name = galaxy.name, coordinate_system = galaxy.coordinate_system, lensing_flag = galaxy.lensing_flag, classification = classifications, notes = galaxy.notes)
    form.classification.data = classifications
    original_id = galaxy.id 
    if form.validate_on_submit ():
        if form.submit.data:
            changes = ""
            removeclass = form.remove_classification.data
            addclass = form.add_classification.data
            for element in removeclass:
                if element in classlist:
                    classlist.remove(element)
                else:
                    flash (element + " was not in the existing list")
            for element in addclass:
                if element not in classlist:
                    classlist.append(element)
                else:
                    flash (element + " already exists")
            newclasslist = ' '.join([str(elem) + ", " for elem in classlist])[:-2]
            if (galaxy.name != form.name.data):
                changes = changes + 'Initial Name: ' + galaxy.name + ' New Name: ' + form.name.data
            if (galaxy.coordinate_system != form.coordinate_system.data):
                changes = changes + 'Initial Coordinate System: ' + galaxy.coordinate_system + ' New Coordinate System: ' + form.coordinate_system.data
            if (galaxy.lensing_flag != form.lensing_flag.data):
                changes = changes + 'Initial Lensing Flag: ' + galaxy.lensing_flag + ' New Lensing Flag: ' + form.lensing_flag.data
            if (galaxy.classification != newclasslist):
                changes = changes + 'Initial Classification: ' + galaxy.classification + ' New Classification: ' + newclasslist
            if (galaxy.notes != form.notes.data):
                try:
                    changes = changes + 'Initial Notes: ' + galaxy.notes + 'New Notes: ' + form.notes.data
                except: 
                    if galaxy.notes == None:
                        changes = changes + 'Initial Notes: ' + "None " + 'New Notes: ' + form.notes.data
                    elif form.notes.data == None:
                        changes = changes + 'Initial Notes: ' + galaxy.notes + 'New Notes: ' + "None"

            galaxy = EditGalaxy(name=form.name.data, right_ascension = galaxy.right_ascension, declination = galaxy.declination, coordinate_system = form.coordinate_system.data, classification = newclasslist, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_edited = changes, original_id = original_id)
            db.session.add(galaxy)
            db.session.commit()

            # Adding the corresponding post
            editgalaxy = session.query(func.max(EditGalaxy.id)).first()
            editgalaxy_id = int(editgalaxy[0])
            post = Post(editgalaxy_id=editgalaxy_id, user_email = current_user.email, time_submitted = datetime.utcnow())
            db.session.add(post)
            db.session.commit()

            flash ('Galaxy has been Edited. ')
        if form.new_line.data:
            return redirect(url_for('main.line_entry_form'))
    return render_template('galaxy_edit_form.html', title= 'Galaxy Edit Form', form=form)

def update_redshift(session, galaxy_id):

    '''
    Update redshift value for a particular galaxy.

    Returns: 
    sum_upper -- returns -1 if redshift could not be calculated, or the sum of weighted redshifts otehrwise (type::float).

    Parameters:
    session -- (type::Session)
    galaxy_id -- id of the galaxy, which redshift has to be updated.
    '''

    line_redshift = session.query(
            Line.emitted_frequency, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
        ).outerjoin(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).all() 

    sum_upper = sum_lower = 0
    for l in line_redshift:

        # Do not account for line entries that either do not have observed frequency value or its positive uncertainty 
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
    # This case passes -1 to change redshift error, which will signal that no change needed
    if sum_lower == 0:
        return -1

    redshift_weighted = sum_upper / sum_lower
    session.query(Galaxy).filter(
        Galaxy.id == galaxy_id
    ).update({"redshift": redshift_weighted})
    session.commit()
    
    return sum_upper

def update_redshift_error(session, galaxy_id, sum_upper):
    
    '''
    Update redshift error value for a particular galaxy.

    Returns: N/A

    Parameters:
    session -- (type::Session)
    galaxy_id -- id of the galaxy, which redshift has to be updated.
    sum_upper -- Sum of weighted redshifts returned by update_redshift. 
    Could be -1 to indicate that the error calculation is unnecessary or (type::float) otherwise.
    '''

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
            redshift_error_weighted = redshift_error_weighted + (weight*delta_z)
        if redshift_error_weighted != 0:
            session.query(Galaxy).filter(
                Galaxy.id == galaxy_id
            ).update({"redshift_error": redshift_error_weighted})
            session.commit()

def redshift_to_frequency(emitted_frequency, z, positive_uncertainty, negative_uncertainty):
    
    '''
    Converts redshift value to frequency.

    Returns:
    nu_obs -- Observed frequency (type::float).
    positive_uncertainty -- Positive uncertainty of the nu_obs value (type::float) or None 

    Parameters:
    emitted_frequency -- emitted frequency value as per dictionary
    z -- submitted redshift value
    positive_uncertainty -- submitted positive uncertainty of the redshift value
    negative_uncertainty -- submitted negative uncertainty of the redshift value

    '''
    
    if z == None:
        return None, None
    nu_obs = emitted_frequency/(z+1)
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

    '''
    Line entry form route
    On access: Returns a form to submit a line entry.
    On submit: If the values areunappropriate, an error is return. 
    If the entry seems to exist already in the database, then no action taken. Otherwise, the entry is uploaded. 
    '''
    name = ""
    form = AddLineForm()
    if form.galaxy_form.data:
        return redirect(url_for('main.galaxy_entry_form'))
    if form.validate_on_submit():
        if form.submit.data:
            session = Session()
            galaxy_id = session.query(Galaxy.id).filter(Galaxy.name==form.galaxy_name.data).scalar()
            try:
                id = galaxy_id
                name = session.query(Galaxy.name).filter(Galaxy.id==id).scalar()
            except:
                id = None
            existed = id
            tempgalaxy_id = None
            
            if galaxy_id == None:
                galaxy_id = session.query(TempGalaxy.id).filter(TempGalaxy.name==form.galaxy_name.data).scalar()
                id = galaxy_id
                name = session.query(TempGalaxy.name).filter(TempGalaxy.id==id).scalar()
                tempgalaxy_id = id
                existed = None
            if galaxy_id==None:
                raise Exception ('Please enter the name exactly as proposed using Caps if necessary')

            try:
                dict_frequency, message = test_frequency(form.emitted_frequency.data, form.species.data)
                if dict_frequency == False:
                    raise Exception (message)
            except:
                pass

            dict_frequency, message = test_frequency(form.emitted_frequency.data, form.species.data)
            if form.freq_type.data == 'z':
                frequency, positive_uncertainty = redshift_to_frequency(dict_frequency, form.observed_line_frequency.data, form.observed_line_frequency_uncertainty_positive.data, form.observed_line_frequency_uncertainty_negative.data)
                negative_uncertainty = None
            else:
                frequency = form.observed_line_frequency.data
                positive_uncertainty = form.observed_line_frequency_uncertainty_positive.data
                negative_uncertainty = form.observed_line_frequency_uncertainty_negative.data

            # Check whether this line entry has been previously uploaded and/or approved
            check_same_temp_line = db.session.query(TempLine.id).filter((TempLine.emitted_frequency == dict_frequency) & (TempLine.observed_line_frequency == frequency) & (TempLine.galaxy_name == form.galaxy_name.data) & (TempLine.species == form.species.data) & (TempLine.integrated_line_flux == to_none(form.integrated_line_flux.data)) & (TempLine.integrated_line_flux_uncertainty_positive == to_none(form.integrated_line_flux_uncertainty_positive.data))).first()


            check_same_line = db.session.query(Line.id).filter((Line.galaxy_id == galaxy_id) & (Line.emitted_frequency == dict_frequency) & (Line.observed_line_frequency == frequency) & (Line.integrated_line_flux == to_none(form.integrated_line_flux.data)) & (Line.integrated_line_flux_uncertainty_positive == to_none(form.integrated_line_flux_uncertainty_positive.data)) & (Line.species == form.species.data)).first()

            # If this galaxy entry has not been previously uploaded and/or approved, then upload. 
            if (check_same_line == None) & (check_same_temp_line == None):
                line = TempLine(galaxy_id=id, 
                                emitted_frequency=form.emitted_frequency.data, 
                                species=form.species.data, 
                                integrated_line_flux = form.integrated_line_flux.data, 
                                integrated_line_flux_uncertainty_positive = form.integrated_line_flux_uncertainty_positive.data,
                                integrated_line_flux_uncertainty_negative = form.integrated_line_flux_uncertainty_negative.data, 
                                peak_line_flux = form.peak_line_flux.data, 
                                peak_line_flux_uncertainty_positive = form.peak_line_flux_uncertainty_positive.data, 
                                peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data, 
                                line_width=form.line_width.data, 
                                line_width_uncertainty_positive = form.line_width_uncertainty_positive.data, 
                                line_width_uncertainty_negative = form.line_width_uncertainty_negative.data, 
                                observed_line_frequency = frequency, 
                                observed_line_frequency_uncertainty_positive = positive_uncertainty, 
                                observed_line_frequency_uncertainty_negative = negative_uncertainty, 
                                detection_type = form.detection_type.data, 
                                observed_beam_major = form.observed_beam_major.data, 
                                observed_beam_minor = form.observed_beam_minor.data, 
                                observed_beam_angle = form.observed_beam_angle.data, 
                                reference = form.reference.data, 
                                notes = form.notes.data, 
                                user_submitted = current_user.username, 
                                user_email = current_user.email, 
                                from_existed_id = existed, 
                                galaxy_name = name,
                                right_ascension = form.right_ascension.data,
                                declination = form.declination.data
                                )
                db.session.add(line)
                db.session.commit()
                templine = session.query(func.max(TempLine.id)).first()
                templine_id = int(templine[0])
                post = Post(templine_id=templine_id, 
                            tempgalaxy_id=tempgalaxy_id, 
                            user_email = current_user.email, 
                            time_submitted = datetime.utcnow()
                            )
                db.session.add(post)
                db.session.commit()
            else:
                pass
            flash ('Line has been added. ')
            return redirect(url_for('main.main'))
    return render_template('line_entry_form.html', title= 'Line Entry Form', form=form)


@bp.route("/line_edit_form/<id>", methods=['GET', 'POST'])
@login_required
def line_edit_form(id):
        
    '''
    Line edit route
    On access: Prefills the form with the desired line to be edited.
    On submit: Submits the edits. An error is raised if unappropriated values are entered. 
    '''

    session = Session ()
    line = session.query(Line).filter(Line.id == id).first()
                    
                    
    name = session.query(Galaxy.name).filter(Galaxy.id==line.galaxy_id).scalar()
    form = EditLineForm(galaxy_name = name, emitted_frequency = line.emitted_frequency, species = line.species, integrated_line_flux = line.integrated_line_flux, integrated_line_flux_uncertainty_positive = line.integrated_line_flux_uncertainty_positive, peak_line_flux = line.peak_line_flux, peak_line_flux_uncertainty_positive = line.peak_line_flux_uncertainty_positive, line_width = line.line_width, line_width_uncertainty_positive = line.line_width_uncertainty_positive, observed_line_frequency = line.observed_line_frequency, observed_line_frequency_uncertainty_positive = line.observed_line_frequency_uncertainty_positive, detection_type = line.detection_type, observed_beam_major = line.observed_beam_major, observed_beam_minor = line.observed_beam_minor, observed_beam_angle = line.observed_beam_angle, reference = line.reference, notes = line.notes)
    if form.galaxy_form.data:
        return redirect(url_for('main.galaxy_entry_form'))
    if form.validate_on_submit():
        if form.submit.data:
            session = Session()
            galaxy_id = session.query(Galaxy.id).filter(Galaxy.name==form.galaxy_name.data).scalar()
            if form.freq_type.data == 'z':
                frequency, positive_uncertainty = redshift_to_frequency(form.emitted_frequency.data, form.observed_line_frequency.data, form.observed_line_frequency_uncertainty_positive.data, form.observed_line_frequency_uncertainty_negative.data)
                negative_uncertainty = None
            else:
                frequency = form.observed_line_frequency.data
                positive_uncertainty = form.observed_line_frequency_uncertainty_positive.data
                negative_uncertainty = form.observed_line_frequency_uncertainty_negative.data

            changes = ""
            if line.emitted_frequency != float (form.emitted_frequency.data):
                changes = changes + "Initial Emitted Frequency: " + str (line.emitted_frequency) + " New Emitted Frequency: " + form.emitted_frequency.data
            if line.species != form.species.data:
                changes = changes + "Initial Species: " + str (line.species) + " New Species: " + form.species.data
            if line.integrated_line_flux !=  float (form.integrated_line_flux.data):
                changes = changes + "Initial Integrated Line Flux: " + line.integrated_line_flux + " New Integrated Line Flux: " + form.integrated_line_flux.data
            if form.integrated_line_flux_uncertainty_positive.data:
                if float (line.integrated_line_flux_uncertainty_positive) != float(form.integrated_line_flux_uncertainty_positive.data):
                    changes = changes + "Initial Integrated Line Flux Positive Uncertainty: " + line.integrated_line_flux_uncertainty_positive + " New Integrated Line Flux Positive Uncertainty: " + form.integrated_line_flux_uncertainty_positive.data
            if form.integrated_line_flux_uncertainty_negative.data:
                if float (line.integrated_line_flux_uncertainty_negative) != float(form.integrated_line_flux_uncertainty_negative.data):
                    changes = changes + "Initial Integrated Line Flux Negative Uncertainty: " + line.integrated_line_flux_uncertainty_negative + " New Integrated Line Flux Negative Uncertainty: " + form.integrated_line_flux_uncertainty_negative.data
            if form.peak_line_flux.data:
                if float(line.peak_line_flux) != float (form.peak_line_flux.data):
                    changes = changes + "Initial Peak Line Flux: " + line.peak_line_flux + " New Peak Line Flux: " + form.peak_line_flux.data
            if form.peak_line_flux_uncertainty_positive.data:
                if float (line.peak_line_flux_uncertainty_positive) != float (form.peak_line_flux_uncertainty_positive.data):
                    changes = changes + "Initial Peak Line Flux Positive Uncertainty: " + line.peak_line_flux_uncertainty_positive + " New Peak Line Flux Positive Uncertainty: " + form.peak_line_flux_uncertainty_positive.data
            if form.peak_line_flux_uncertainty_negative.data:
                if float (line.peak_line_flux_uncertainty_negative) != float (form.peak_line_flux_uncertainty_negative.data):
                    changes = changes + "Initial Peak Line Flux Negative Uncertainty: " + line.peak_line_flux_uncertainty_negative + " New Peak Line Flux Negative Uncertainty: " + form.peak_line_flux_uncertainty_negative.data
            if form.line_width.data:
                if float (line.line_width) != float (form.line_width.data):
                    changes = changes + "Initial Line Width: " + line.line_width + " New Line Width: " + form.line_width.data
            if form.line_width_uncertainty_positive.data:
                if float (line.line_width_uncertainty_positive) != float (form.line_width_uncertainty_positive.data):
                    changes = changes + "Initial Line Width Positive Uncertainty: " + line.line_width_uncertainty_positive + " New Line Width Positive Uncertainty: " + form.line_width_uncertainty_positive.data
            if form.line_width_uncertainty_negative.data:
                if float (line.line_width_uncertainty_negative) != float (form.line_width_uncertainty_negative.data):
                    changes = changes + "Initial Line Width Negative Uncertainty: " + line.line_width_uncertainty_negative + " New Line Width Negative Uncertainty: " + form.line_width_uncertainty_negative.data
            if form.observed_line_frequency.data:
                if float (line.observed_line_frequency) != float (form.observed_line_frequency.data):
                    changes = changes + "Initial Observed Line Frequency: " + line.observed_line_frequency + " New Observed Line Frequency: " + form.observed_line_frequency.data
            if form.observed_line_frequency_uncertainty_positive.data:
                if float (line.observed_line_frequency_uncertainty_positive) != float (form.observed_line_frequency_uncertainty_positive.data):
                    changes = changes + "Initial Observed Line Frequency Positive Uncertainty: " + line.observed_line_frequency_uncertainty_positive + " New Observed Line Frequency Positive Uncertainty: " + form.observed_line_frequency_uncertainty_positive.data
            if form.observed_line_frequency_uncertainty_negative.data:
                if float (line.observed_line_frequency_uncertainty_negative) != float (form.observed_line_frequency_uncertainty_negative.data):
                    changes = changes + "Initial Observed Line Frequency Negative Uncertainty: " + line.observed_line_frequency_uncertainty_negative + " New Observed Line Frequency Negative Uncertainty: " + form.observed_line_frequency_uncertainty_negative.data
            if form.detection_type.data:
                if line.detection_type != form.detection_type.data:
                    changes = changes + "Initial Detection Type: " + line.detection_type + " New Detection Type: " + form.detection_type.data
            if form.observed_beam_major.data:
                if float (line.observed_beam_major) != float (form.observed_beam_major.data):
                    changes = changes + "Initial Observed Beam Major: " + line.observed_beam_major + " New Observed Beam Major: " + form.observed_beam_major.data
            if form.observed_beam_minor.data:
                if float (line.observed_beam_minor) != float (form.observed_beam_minor.data):
                    changes = changes + "Initial Observed Beam Minor: " + line.observed_beam_minor + " New Observed Beam Minor: " + form.observed_beam_minor.data
            if form.observed_beam_angle.data:
                if float (line.observed_beam_angle) != float (form.observed_beam_angle.data):
                    changes = changes + "Initial Observed Beam Angle: " + line.observed_beam_angle + " New Observed Beam Angle: " + form.observed_beam_angle.data
            if form.reference.data:
                if line.reference != form.reference.data:
                    changes = changes + "Initial Reference: " + line.reference + " New Reference: " + form.reference.data
            if form.notes.data:
                if line.notes != form.notes.data:
                    changes = changes + "Initial Notes: " + line.notes + " New Notes: " + form.notes.data
            line = EditLine(galaxy_id=galaxy_id, emitted_frequency=form.emitted_frequency.data, species=form.species.data, integrated_line_flux = form.integrated_line_flux.data, integrated_line_flux_uncertainty_positive = form.integrated_line_flux_uncertainty_positive.data, integrated_line_flux_uncertainty_negative = form.integrated_line_flux_uncertainty_negative.data, peak_line_flux = form.peak_line_flux.data, peak_line_flux_uncertainty_positive = form.peak_line_flux_uncertainty_positive.data, peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data, line_width=form.line_width.data, line_width_uncertainty_positive = form.line_width_uncertainty_positive.data, line_width_uncertainty_negative = form.line_width_uncertainty_negative.data, observed_line_frequency = frequency, observed_line_frequency_uncertainty_positive = positive_uncertainty, observed_line_frequency_uncertainty_negative = negative_uncertainty, detection_type = form.detection_type.data, observed_beam_major = form.observed_beam_major.data, observed_beam_minor = form.observed_beam_minor.data, observed_beam_angle = form.observed_beam_angle.data, reference = form.reference.data, notes = form.notes.data, user_submitted = current_user.username, user_email = current_user.email, is_edited = changes)
            db.session.add(line)
            db.session.commit()

            # Add the corresponding post
            editline = session.query(func.max(EditLine.id)).first()
            editline_id = int(editline[0])
            post = Post(editline_id=editline_id, galaxy_id=galaxy_id, user_email = current_user.email, time_submitted = datetime.utcnow())
            db.session.add(post)
            db.session.commit()

            flash ('Line has been edited. ')
            return redirect(url_for('main.main'))
    return render_template('line_edit_form.html', title= 'Line Edit Form', form=form)

@bp.route('/galaxies')
@login_required
def galaxydic():

    '''
    '''

    session = Session()
    res1 = session.query(Galaxy)
    res2 = session.query(TempGalaxy)
    list_galaxies = [r.as_dict() for r in res1]
    list_temp_galaxies = [r.as_dict() for r in res2]
    list_galaxies.extend(list_temp_galaxies)
    return jsonify(list_galaxies)

@bp.route('/approvedgalaxies')
@login_required
def galaxies():

    '''
    '''

    session = Session()
    res = session.query(Galaxy)
    list_galaxies = [r.as_dict() for r in res]
    return jsonify(list_galaxies)

@bp.route('/process', methods=['POST'])
@login_required
def process():
    galaxy_name = request.form['galaxy_name']
    if galaxy_name:
        return jsonify({'galaxy_name':galaxy_name})
    return jsonify({'error': 'missing data..'})

@bp.route('/galaxy/<name>', methods=['GET', 'POST'])
def galaxy(name):

    '''
    Galaxy page route
    On access: Displays data of a particular galaxy and its corresponding line entries.
    '''

    session = Session ()
    galaxy = Galaxy.query.filter_by(name=name).first_or_404()
    line = session.query(Line).filter_by(galaxy_id = galaxy.id).all()

    return render_template('galaxy.html', galaxy=galaxy, line = line)


@bp.route("/submit")
@login_required
def submit():
    return render_template("submit.html")

@bp.route("/convert_to_CSV/<table>/<identifier>", methods=['GET', 'POST'])
@login_required
def convert_to_CSV(table, identifier):

    '''
    Converts a query to CSV route
    ON access: Returns a .csv file with the data of a query. Query is determined by the argument <table>.
    '''

    if table == "Galaxy":
        
        # Galaxy takes averaged coordinates
        f = open('galaxy.csv', 'w')
        out = csv.writer(f)
        out.writerow([
            COL_NAMES['name'], 
            COL_NAMES['right_ascension'], 
            COL_NAMES['declination'], 
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
        response.mimetype='text/csv'
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
            COL_NAMES['observed_line_frequency'],
            COL_NAMES['observed_line_frequency_uncertainty_positive'],
            COL_NAMES['observed_line_frequency_uncertainty_negative'],
            COL_NAMES['detection_type'],
            COL_NAMES['observed_beam_major'],
            COL_NAMES['observed_beam_minor'],
            COL_NAMES['observed_beam_angle'],
            COL_NAMES['reference'],
            COL_NAMES['l_notes']
            ])
        for item in Line.query.all():
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
                item.observed_line_frequency,
                item.observed_line_frequency_uncertainty_positive,
                item.observed_line_frequency_uncertainty_negative,
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
        response.mimetype='text/csv'
        return response

    elif table == "Galaxy Lines":

        # Galaxy with lines takes lines individual coordinates
        session = Session ()
        f = open('galaxy_lines.csv', 'w')
        out = csv.writer(f)
        galaxy_lines = session.query(Galaxy, Line).outerjoin(Galaxy).filter(Galaxy.id == identifier, Line.galaxy_id == identifier)
        out.writerow([
            COL_NAMES['name'], 
            COL_NAMES['right_ascension'], 
            COL_NAMES['declination'], 
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
            COL_NAMES['observed_line_frequency'],
            COL_NAMES['observed_line_frequency_uncertainty_positive'],
            COL_NAMES['observed_line_frequency_uncertainty_negative'],
            COL_NAMES['detection_type'],
            COL_NAMES['observed_beam_major'],
            COL_NAMES['observed_beam_minor'],
            COL_NAMES['observed_beam_angle'],
            COL_NAMES['reference'],
            COL_NAMES['l_notes']
            ])
        for item in galaxy_lines:
            l = item [1]
            g = item [0]
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
                l.observed_line_frequency,
                l.observed_line_frequency_uncertainty_positive,
                l.observed_line_frequency_uncertainty_negative,
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
        response.mimetype='text/csv'
        return response

    elif table == "Everything":

        # Lines take individual coordinates
        session = Session ()
        f = open('galaxies_lines.csv', 'w')
        out = csv.writer(f)
        data = session.query(Galaxy, Line).outerjoin(Line)
        out.writerow([
            COL_NAMES['name'], 
            COL_NAMES['right_ascension'], 
            COL_NAMES['declination'], 
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
            COL_NAMES['observed_line_frequency'],
            COL_NAMES['observed_line_frequency_uncertainty_positive'],
            COL_NAMES['observed_line_frequency_uncertainty_negative'],
            COL_NAMES['detection_type'],
            COL_NAMES['observed_beam_major'],
            COL_NAMES['observed_beam_minor'],
            COL_NAMES['observed_beam_angle'],
            COL_NAMES['reference'],
            COL_NAMES['l_notes']
            ])
        for item in data:
            l = item [1]
            g = item [0]
            if l is not None:
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
                    l.observed_line_frequency,
                    l.observed_line_frequency_uncertainty_positive,
                    l.observed_line_frequency_uncertainty_negative,
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
        response.mimetype='text/csv'
        return response
    elif table == "Empty":
        session = Session ()
        f = open('sample.csv', 'w')
        out = csv.writer(f)
        out.writerow(['name', 'right_ascension', 'declination', 'coordinate_system', 'lensing_flag', 'classification', 'notes', 'emitted_frequency', 'species', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'integrated_line_flux_uncertainty_negative', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'peak_line_flux_uncertainty_negative', 'line_width', 'line_width_uncertainty_positive', 'line_width_uncertainty_negative', 'freq_type', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'observed_line_frequency_uncertainty_negative', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        f.close()
        with open('./sample.csv', 'r') as file:
            sample_csv = file.read()
        response = make_response(sample_csv)
        cd = 'attachment; filename=sample.csv'
        response.headers['Content-Disposition'] = cd 
        response.mimetype='text/csv'
        return response     