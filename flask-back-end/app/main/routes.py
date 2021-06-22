from sqlalchemy.sql.expression import outerjoin, true
from app import db, Session, engine
from flask import render_template, flash, redirect, url_for, request, g, make_response, jsonify, json
from flask_login import current_user, login_required
from app.models import Galaxy, User, Line
from app.main.forms import EditProfileForm, SearchForm, AddGalaxyForm, AddLineForm, AdvancedSearchForm, UploadFileForm
from werkzeug.urls import url_parse
import csv
from sqlalchemy import func
from sqlalchemy.sql import text
from config import EMITTED_FREQUENCY
from io import TextIOWrapper
import math
from app.main import bp

#The last-seen functionality (if necessary), otherwise it could still be useful of any before_request functionality
#@app.before_request
#def before_request():
    #if current_user.is_authenticated:
        #g.search_form = SearchForm()

#default route
@bp.route("/")
@bp.route("/home")
def home():
    return render_template("/home.html")

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.university = form.university.data
        current_user.website = form.website.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash ("Your changes have been submitted")
        return redirect(url_for('main'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.university.data = current_user.university
        form.website.data = current_user.website
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form, user=user)

@bp.route('/test')
@login_required
def test():
    #conn = engine.connect()    
    #session = Session(bind=conn)
    session = Session()
    galaxies = session.query(Galaxy).filter(text('cos(Galaxy.declination)<0.8')).all()
    return render_template("/test.html", galaxies=galaxies)

@bp.route("/main", methods=['GET', 'POST'])
@login_required
def main():
    if current_user.is_authenticated:
        form = SearchForm()
    return render_template("/main.html", galaxy = Galaxy.query.all(), line = Line.query.all(), form=form)

def to_empty(entry):
    if entry == None:
        entry = ''
    else:
        entry = entry
    return entry

def to_m_inf(entry):
    if entry == None:
        entry = float('-inf')
    elif entry == '':
        entry = '-inf'
    else:
        entry = entry
    return entry

def to_p_inf(entry):
    if entry == None:
        entry = float('inf')
    elif entry == '':
        entry = 'inf'
    else:
        entry = entry
    return entry

def to_zero(entry):
    if entry == None:
        entry = 0
    else:
        entry = entry
    return entry

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
        if form_advanced.line_id_type.data == None:
            form_advanced.line_id_type.data = ''
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
                galaxies=session.query(Galaxy, Line).outerjoin(Line).filter(func.acos(func.sin(func.radians(ra_to_float(form_advanced.right_ascension_point.data))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_advanced.right_ascension_point.data))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_advanced.declination_point.data) - Galaxy.declination)))   ) < distance)
                
            else:
                galaxies=session.query(Galaxy, Line).outerjoin(Line)

            #Filters in respect to galaxy parameters
            galaxies=galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)), ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (Galaxy.declination.between(dec_to_float(to_m_inf(form_advanced.declination_min.data)), dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data) | (Galaxy.redshift == None) ) & (Galaxy.lensing_flag.contains(form_advanced.lensing_flag.data) | (Galaxy.lensing_flag == None)))

            #Filters in respect to line parameters or if galaxy has no lines
            galaxies = galaxies.filter((Line.id == None) | ((Line.j_upper.between(form_advanced.j_upper_min.data, form_advanced.j_upper_max.data) | (Line.j_upper == None )) & (Line.line_id_type.contains(form_advanced.line_id_type.data) | (Line.line_id_type == None)) & (Line.integrated_line_flux.between(form_advanced.integrated_line_flux_min.data, form_advanced.integrated_line_flux_max.data) | (Line.integrated_line_flux == None)) & (Line.peak_line_flux.between(form_advanced.peak_line_flux_min.data, form_advanced.peak_line_flux_max.data) | (Line.peak_line_flux == None)) & (Line.line_width.between(form_advanced.line_width_min.data, form_advanced.line_width_max.data) | (Line.line_width == None )) & (Line.observed_line_frequency.between(form_advanced.observed_line_frequency_min.data, form_advanced.observed_line_frequency_max.data) | (Line.observed_line_frequency == None )) & (Line.detection_type.contains(form_advanced.detection_type.data) | (Line.detection_type == None)) & (Line.observed_beam_major.between(form_advanced.observed_beam_major_min.data, form_advanced.observed_beam_major_max.data) | (Line.observed_beam_major == None )) & (Line.observed_beam_minor.between(form_advanced.observed_beam_minor_min.data, form_advanced.observed_beam_minor_max.data) | (Line.observed_beam_minor == None )) & (Line.reference.contains(form_advanced.reference.data) | (Line.reference == None)) ))

            galaxies = galaxies.distinct(Galaxy.name).group_by(Galaxy.name).order_by(Galaxy.name).all()

            return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)   

            
        
        elif form_advanced.lineSearch.data:
            if (form_advanced.right_ascension_point.data != None) and (form_advanced.declination_point.data != None) and ((form_advanced.radius_d.data != None) or (form_advanced.radius_m.data != None) or (form_advanced.radius_s.data != None)):
                distance=math.radians(to_zero(form_advanced.radius_d.data)+to_zero(form_advanced.radius_m.data)/60+to_zero(form_advanced.radius_s.data)/3600) 
                galaxies=session.query(Galaxy, Line).outerjoin(Galaxy).filter(func.acos(func.sin(func.radians(ra_to_float(form_advanced.right_ascension_point.data))) * func.sin(func.radians(Galaxy.right_ascension)) + func.cos(func.radians(ra_to_float(form_advanced.right_ascension_point.data))) * func.cos(func.radians(Galaxy.right_ascension)) * func.cos(func.radians(func.abs(dec_to_float(form_advanced.declination_point.data) - Galaxy.declination)))   ) < distance)
                
            else:
                galaxies=session.query(Galaxy, Line).outerjoin(Galaxy)


            galaxies=galaxies.filter(Galaxy.name.contains(form_advanced.name.data) & (Galaxy.right_ascension.between(ra_to_float(to_m_inf(form_advanced.right_ascension_min.data)), ra_to_float(to_p_inf(form_advanced.right_ascension_max.data)))) & (Galaxy.declination.between(dec_to_float(to_m_inf(form_advanced.declination_min.data)), dec_to_float(to_p_inf(form_advanced.declination_max.data)))) & (Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data) | (Galaxy.redshift == None) ) & (Galaxy.lensing_flag.contains(form_advanced.lensing_flag.data) | (Galaxy.lensing_flag == None)))

            galaxies=galaxies.filter((Line.j_upper.between(form_advanced.j_upper_min.data, form_advanced.j_upper_max.data) | (Line.j_upper == None )) & (Line.line_id_type.contains(form_advanced.line_id_type.data) | (Line.line_id_type == None)) & (Line.integrated_line_flux.between(form_advanced.integrated_line_flux_min.data, form_advanced.integrated_line_flux_max.data) | (Line.integrated_line_flux == None)) & (Line.peak_line_flux.between(form_advanced.peak_line_flux_min.data, form_advanced.peak_line_flux_max.data) | (Line.peak_line_flux == None)) & (Line.line_width.between(form_advanced.line_width_min.data, form_advanced.line_width_max.data) | (Line.line_width == None )) & (Line.observed_line_frequency.between(form_advanced.observed_line_frequency_min.data, form_advanced.observed_line_frequency_max.data) | (Line.observed_line_frequency == None )) & (Line.detection_type.contains(form_advanced.detection_type.data) | (Line.detection_type == None)) & (Line.observed_beam_major.between(form_advanced.observed_beam_major_min.data, form_advanced.observed_beam_major_max.data) | (Line.observed_beam_major == None )) & (Line.observed_beam_minor.between(form_advanced.observed_beam_minor_min.data, form_advanced.observed_beam_minor_max.data) | (Line.observed_beam_minor == None )) & (Line.reference.contains(form_advanced.reference.data) | (Line.reference == None)) )
            
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
        csv_file = TextIOWrapper(csvfile, encoding='utf-8')
        reader = csv.DictReader(csv_file)
        data = [row for row in reader]
        if data == []:
            flash ("CSV File is empty. ")
        g_validated = True
        for row in data:
            if row['name'] == "":
                g_validated = False
                flash ("Galaxy Name is Mandatory")
            if row['coordinate_system'] != "ICRS" and row['coordinate_system'] != "J2000":
                g_validated = False
                flash ("Coordinate System can be ICRS or J2000 only.")
            if row['lensing_flag'] != "Lensed" and row['coordinate_system'] != "Unlensed" and row['coordinate_system'] != "Either":
                g_validated = False
                flash ("Please enter either \"Lensed\", \"Unlensed\" or \"Either\" under Lensing Flag.")
            if row['classification'] == "":
                g_validated = False
                flash ("Classification is Mandatory")
            if row['right_ascension'] == "":
                g_validated = False
                flash ("Right Ascension is Mandatory")
            if row['declination'] == "":
                g_validated = False
                flash ("Declination is Mandatory")
            if row['redshift'] == "":
                g_validated = False
                flash ("Redshift is Mandatory.")
            if int(row['redshift']) <1 :
                g_validated = False
                flash ("Redshift cannot be negative.")
            if g_validated == True:
                galaxy = Galaxy(name = row['name'],
                                right_ascension = row['right_ascension'],
                                declination = row['declination'],
                                coordinate_system = row['coordinate_system'],
                                redshift = row['redshift'],
                                lensing_flag = row ['lensing_flag'],
                                classification = row ['classification'],
                                notes = row ['notes'])
                db.session.add(galaxy)
                new_id = db.session.query(func.max(Galaxy.id)).first()
                id = new_id [0]
                l_validated = True
                if row['j_upper'] == "":
                    l_validated = False
                    flash ("J Upper is Mandatory")
                if row['integrated_line_flux'] == "":
                    l_validated = False
                    flash ("Integrated Line Flux is Mandatory")
                if row['integrated_line_flux_uncertainty_positive'] == "":
                    l_validated = False
                    flash ("Integrated Line Flux Positive Uncertainty is Mandatory")
                if row['integrated_line_flux_uncertainty_negative'] == "":
                    l_validated = False
                    flash ("Integrated Line Flux Negative Uncertainty is Mandatory")
                if int (row['integrated_line_flux_uncertainty_positive']) < 0:
                    l_validated = False
                    flash ("Integrated Line Flux Positive Uncertainty must be Positive")
                if int (row['integrated_line_flux_uncertainty_negative']) > 0:
                    l_validated = False
                    flash ("Integrated Line Flux Negative Uncertainty must be Negative")
                if row ['peak_line_flux_uncertainty_positive'] != "":
                    if int (row ['peak_line_flux_uncertainty_positive']) < 0:
                        l_validated = False
                        flash ("Peak Line Flux Positive Uncertainty must be Positive")
                if row ['peak_line_flux_uncertainty_negative'] != "":
                    if int (row ['peak_line_flux_uncertainty_negative']) > 0:
                        l_validated = False
                        flash ("Peak Line Flux Negative Uncertainty must be Negative")
                if row ['line_width_uncertainty_positive'] != "":
                    if int (row ['line_width_uncertainty_positive']) < 0:
                        l_validated = False
                        flash ("Line Width Positive Uncertainty must be Positive")
                if row ['line_width_uncertainty_negative'] != "":
                    if int (row ['line_width_uncertainty_negative']) > 0:
                        l_validated = False
                        flash ("Line Width Negative Uncertainty must be Negative")
                if row ['observed_line_frequency_uncertainty_positive'] != "":
                    if int (row ['observed_line_frequency_uncertainty_positive']) < 0:
                        l_validated = False
                        flash ("Observed Line Frequency Positive Uncertainty must be Positive")
                if row ['observed_line_frequency_uncertainty_negative'] != "":
                    if int (row ['observed_line_frequency_uncertainty_negative']) > 0:
                        l_validated = False
                        flash ("Observed Line Frequency Negative Uncertainty must be Negative")
                if l_validated == True:
                    line = Line (galaxy_id = id,
                                j_upper= row ['j_upper'], 
                                line_id_type = row ['line_id_type'], 
                                integrated_line_flux = row ['integrated_line_flux'], 
                                integrated_line_flux_uncertainty_positive = row ['integrated_line_flux_uncertainty_positive'], 
                                integrated_line_flux_uncertainty_negative = row ['integrated_line_flux_uncertainty_negative'], 
                                peak_line_flux = row ['peak_line_flux'],
                                peak_line_flux_uncertainty_positive = row ['peak_line_flux_uncertainty_positive'],
                                peak_line_flux_uncertainty_negative= row ['peak_line_flux_uncertainty_negative'], 
                                line_width= row ['line_width'],
                                line_width_uncertainty_positive = row ['line_width_uncertainty_positive'],
                                line_width_uncertainty_negative = row ['line_width_uncertainty_negative'],
                                observed_line_frequency = row ['observed_line_frequency'],
                                observed_line_frequency_uncertainty_positive = row ['observed_line_frequency_uncertainty_positive'],
                                observed_line_frequency_uncertainty_negative = row ['observed_line_frequency_uncertainty_negative'],
                                detection_type = row ['detection_type'],
                                observed_beam_major = row ['observed_beam_major'], 
                                observed_beam_minor = row ['observed_beam_minor'],
                                observed_beam_angle = row ['observed_beam_angle'],
                                reference = row ['reference'],
                                notes = row ['notes']
                                )
                    db.session.add(line)
                    db.session.commit()
                    session = Session ()
                    total = update_redshift(session, id)
                    update_redshift_error(session, id, total)
                    flash ("File has been successfully uploaded. ")
    return render_template ("/entry_file.html", title = "Upload File", form = form)
     


def ra_to_float(coordinates):
    if coordinates.find('s') != -1:
        h = float(coordinates[0:2])
        m = float(coordinates[3:5])
        s = float(coordinates[coordinates.find('m')+1:coordinates.find('s')])
        return h*15+m/4+s/240
    elif coordinates == '-inf':
        return float('-inf')
    elif coordinates == 'inf':
        return float('inf')
    else:
        ra = coordinates
        return float(ra) 
def dec_to_float(coordinates):
    if coordinates.find('s') != -1:
        d = float(coordinates[1:3])
        m = float(coordinates[4:6])
        s = float(coordinates[coordinates.find('m')+1:coordinates.find('s')])
        if coordinates[0] == "-":
            return (-1)*(d+m/60+s/3600)
        else:
            return d+m/60+s/3600
    elif coordinates == '-inf':
        return float('-inf')
    elif coordinates == 'inf':
        return float('inf')
    else:
        dec = coordinates
        return float(dec)



@bp.route("/galaxy_entry_form", methods=['GET', 'POST'])
@login_required
def galaxy_entry_form():
    form = AddGalaxyForm()
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
            galaxy = Galaxy(name=form.name.data, right_ascension=RA, declination = DEC, coordinate_system = form.coordinate_system.data, redshift = form.redshift.data, classification = form.classification.data, lensing_flag = form.lensing_flag.data, notes = form.notes.data, user = current_user.username, user_email = current_user.email)
            db.session.add(galaxy)
            db.session.commit()
            flash ('Galaxy has been added. ')
        if form.new_line.data:
            return redirect(url_for('line_entry_form'))
    return render_template('galaxy_entry_form.html', title= 'Galaxy Entry Form', form=form)

def update_redshift(session, galaxy_id):
    line_redshift = session.query(
            Line.j_upper, Line.observed_line_frequency, Line.observed_line_frequency_uncertainty_negative, Line.observed_line_frequency_uncertainty_positive
        ).outerjoin(Galaxy).filter(
            Galaxy.id == galaxy_id
        ).all() 

    sum_upper = sum_lower = 0
    for l in line_redshift:
        delta_nu = l.observed_line_frequency_uncertainty_positive - l.observed_line_frequency_uncertainty_negative
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
        delta_nu = l.observed_line_frequency_uncertainty_positive - l.observed_line_frequency_uncertainty_negative
        J_UPPER = l.j_upper
        z = (EMITTED_FREQUENCY.get(J_UPPER) - l.observed_line_frequency) / l.observed_line_frequency
        delta_z = ((1 + z) * delta_nu) / l.observed_line_frequency
        weight = (z/delta_z)/sum_upper
        redshift_error_weighted = redshift_error_weighted =+ (weight*delta_z)
    session.query(Galaxy).filter(
        Galaxy.id == galaxy_id
    ).update({"redshift_error": redshift_error_weighted})
    session.commit()

@bp.route("/line_entry_form", methods=['GET', 'POST'])
@login_required
def line_entry_form():
    form = AddLineForm()
    if form.galaxy_form.data:
        return redirect(url_for('galaxy_entry_form'))
    if form.validate_on_submit():
        if form.submit.data:
            session = Session()
            galaxy_id = session.query(Galaxy.id).filter(Galaxy.name==form.galaxy_name.data).scalar()
            line = Line(galaxy_id=galaxy_id, j_upper=form.j_upper.data, line_id_type = form.line_id_type.data, integrated_line_flux = form.integrated_line_flux.data, integrated_line_flux_uncertainty_positive = form.integrated_line_flux_uncertainty_positive.data, integrated_line_flux_uncertainty_negative = form.integrated_line_flux_uncertainty_negative.data, peak_line_flux = form.peak_line_flux.data, peak_line_flux_uncertainty_positive = form.peak_line_flux_uncertainty_positive.data, peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data, line_width=form.line_width.data, line_width_uncertainty_positive = form.line_width_uncertainty_positive.data, line_width_uncertainty_negative = form.line_width_uncertainty_negative.data, observed_line_frequency = form.observed_line_frequency.data, observed_line_frequency_uncertainty_positive = form.observed_line_frequency_uncertainty_positive.data, observed_line_frequency_uncertainty_negative = form.observed_line_frequency_uncertainty_negative.data, detection_type = form.detection_type.data, observed_beam_major = form.observed_beam_major.data, observed_beam_minor = form.observed_beam_minor.data, observed_beam_angle = form.observed_beam_angle.data, reference = form.reference.data, notes = form.notes.data, user = current_user.username, user_email = current_user.email)
            db.session.add(line)
            db.session.commit()
            total = update_redshift(session, galaxy_id)
            update_redshift_error(session, galaxy_id, total)
            flash ('Line has been added. ')
            return redirect(url_for('main'))
    return render_template('line_entry_form.html', title= 'Line Entry Form', form=form)

@bp.route('/galaxies')
@login_required
def galaxydic():
    res = Galaxy.query.all()
    list_galaxies = [r.as_dict() for r in res]
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
    return render_template('galaxy.html', galaxy=galaxy, line = line)

@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@bp.route("/submit")
@login_required
def submit():
    return render_template("submit.html")

@bp.route("/convert_to_CSV/<table>/<identifier>", methods=['GET', 'POST'])
@login_required
def convert_to_CSV(table, identifier):
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
        out.writerow(['galaxy_id', 'line_id_type', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'integrated_line_flux_uncertainty_negative', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'peak_line_flux_uncertainty_negative', 'line_width', 'line_width_uncertainty_positive', 'line_width_uncertainty_negative', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'observed_line_frequency_uncertainty_negative', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        for item in Line.query.all():
            out.writerow([item.galaxy_id, item.line_id_type, item.integrated_line_flux, item.integrated_line_flux_uncertainty_positive, item.integrated_line_flux_uncertainty_negative, item.peak_line_flux, item.peak_line_flux_uncertainty_positive, item.peak_line_flux_uncertainty_negative, item.line_width, item.line_width_uncertainty_positive, item.line_width_uncertainty_negative, item.observed_line_frequency, item.observed_line_frequency_uncertainty_positive, item.observed_line_frequency_uncertainty_negative, item.detection_type, item.observed_beam_major, item.observed_beam_minor, item.observed_beam_angle, item.reference, item.notes])
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
        out.writerow(['id', 'name', 'right_ascension', 'declination', 'coordinate_system', 'redshift', 'lensing_flag', 'classification', 'notes', 'j_upper', 'line_id_type', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'integrated_line_flux_uncertainty_negative', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'peak_line_flux_uncertainty_negative', 'line_width', 'line_width_uncertainty_positive', 'line_width_uncertainty_negative', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'observed_line_frequency_uncertainty_negative', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        for item in galaxy_lines:
            l = item [1]
            g = item [0]
            out.writerow([g.id, g.name, g.right_ascension, g.declination, g.coordinate_system, g.redshift, g.lensing_flag, g.classification, g.notes, l.j_upper, l.line_id_type, l.integrated_line_flux, l.integrated_line_flux_uncertainty_positive, l.integrated_line_flux_uncertainty_negative, l.peak_line_flux, l.peak_line_flux_uncertainty_positive, l.peak_line_flux_uncertainty_negative, l.line_width, l.line_width_uncertainty_positive, l.line_width_uncertainty_negative, l.observed_line_frequency, l.observed_line_frequency_uncertainty_positive, l.observed_line_frequency_uncertainty_negative, l.detection_type, l.observed_beam_major, l.observed_beam_minor, l.observed_beam_angle, l.reference, l.notes])
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
        out.writerow(['name', 'right_ascension', 'declination', 'coordinate_system', 'redshift', 'lensing_flag', 'classification', 'notes', 'j_upper', 'line_id_type', 'integrated_line_flux', 'integrated_line_flux_uncertainty_positive', 'integrated_line_flux_uncertainty_negative', 'peak_line_flux', 'peak_line_flux_uncertainty_positive', 'peak_line_flux_uncertainty_negative', 'line_width', 'line_width_uncertainty_positive', 'line_width_uncertainty_negative', 'observed_line_frequency', 'observed_line_frequency_uncertainty_positive', 'observed_line_frequency_uncertainty_negative', 'detection_type', 'observed_beam_major', 'observed_beam_minor', 'observed_beam_angle', 'reference', 'notes'])
        f.close()
        with open('./sample.csv', 'r') as file:
            sample_csv = file.read()
        response = make_response(sample_csv)
        cd = 'attachment; filename=sample.csv'
        response.headers['Content-Disposition'] = cd 
        response.mimetype='text/csv'
        return response

    