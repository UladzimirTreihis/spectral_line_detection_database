from app import app, db
from flask import render_template, flash, redirect, url_for, request, g, make_response
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Galaxy, User, Line
from app.forms import LoginForm, RegistrationForm, EditProfileForm, SearchForm, AddGalaxyForm, AddLineForm, ButtonForm, AdvancedSearchForm
from werkzeug.urls import url_parse
from datetime import datetime
import csv
from werkzeug.wrappers import Response
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import or_, and_

#The last-seen functionality (if necessary), otherwise it could still be useful of any before_request functionality
#@app.before_request
#def before_request():
    #if current_user.is_authenticated:
        #g.search_form = SearchForm()

#default route
@app.route("/")
@app.route("/home")
def home():
    return render_template("/home.html")

#log-in route
@app.route("/login", methods=['GET', 'POST'])
def login():
    #if user is already authenticated, the log-in address redirects to home
    if current_user.is_authenticated: 
      return redirect(url_for('home'))
    #form becomes an instance of LoginForm function
    form = LoginForm()
    if form.validate_on_submit():
        #creating local user object
        user = User.query.filter_by(username=form.username.data).first()
        #If user does not exist or username/password incorrect -> redirect to log-in again
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        #If the condition above was false, it logs-in the user and checks the remember me info; redicrects to the temporal login_successful page.
        login_user(user, remember=form.remember_me.data)
        #the code for redirection back to @index once logged-in successfully
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main')
        return redirect(next_page)
    return render_template("./auth/login.html", title='Sign In', form=form)

@app.route("/main", methods=['GET', 'POST'])
@login_required
def main():
    if current_user.is_authenticated:
        form = SearchForm()
        form_button = ButtonForm()
        form_advanced = AdvancedSearchForm()

    if request.method == 'POST':
        if request.form['advanced_search'] == 'Advanced Search':
            return render_template("/main.html", galaxy = Galaxy.query.all(), line = Line.query.all(), form=form, form_button=form_button, form_advanced=form_advanced)
    return render_template("/main.html", galaxy = Galaxy.query.all(), line = Line.query.all(), form=form, form_button=form_button)

@app.route("/entry_file")
@login_required
def entry_file():
    return render_template("/entry_file.html")

@app.route("/entry_form")
@login_required
def entry_form():
    return render_template("/entry_form.html")
    
#Is expected to redirect here to display the results. 
@app.route("/query_results", methods=['GET', 'POST'])
@login_required
def query_results():
    #if request.method == 'POST' or 'GET':
        #return 'It was a post request'
    if current_user.is_authenticated:
        form = SearchForm()
        form_advanced = AdvancedSearchForm()
        form_button = ButtonForm()
    
    if request.method == 'POST':
        #if request.form['advanced_search'] == 'Advanced Search':
            #return render_template("/query_results.html", form=form, form_button=form_button, form_advanced=form_advanced)
        if form_advanced.name.data == None:
            form_advanced.name.data = ''
        if form_advanced.right_ascension_min.data == None:
            form_advanced.right_ascension_min.data = float('-inf')
        if form_advanced.right_ascension_max.data == None:
            form_advanced.right_ascension_max.data = float('inf')
        if form_advanced.declination_min.data == None:
            form_advanced.declination_min.data = float('-inf')
        if form_advanced.declination_max.data == None:
            form_advanced.declination_max.data = float('inf')
        if form_advanced.redshift_min.data == None:
            form_advanced.redshift_min.data = float('-inf')
        if form_advanced.redshift_max.data == None:
            form_advanced.redshift_max.data = float('inf')
        if form_advanced.lensing_flag.data == None:
            form_advanced.lensing_flag.data = ''
        

        if form_advanced.submit:
            galaxies = Galaxy.query.filter(Galaxy.name.contains(form_advanced.name.data), (or_(Galaxy.right_ascension.between(form_advanced.right_ascension_min.data, form_advanced.right_ascension_max.data), Galaxy.right_ascension == None )), (or_(Galaxy.declination.between(form_advanced.declination_min.data, form_advanced.declination_max.data), Galaxy.declination == None )), (or_(Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data), Galaxy.redshift == None )), (or_(Galaxy.lensing_flag.contains(form_advanced.lensing_flag.data), Galaxy.lensing_flag == None)))
            #return str(form_advanced.name.data)+' '+str(form_advanced.right_ascension_min.data)+' '+str(form_advanced.right_ascension_max.data)+' '+str(form_advanced.declination_min.data)+' '+str(form_advanced.declination_max.data)+' '+str(form_advanced.redshift_min.data)+' '+str(form_advanced.redshift_max.data)+' '+str(form_advanced.lensing_flag.data)
        
    
            
        elif form.submit:
            galaxies = Galaxy.query.filter(Galaxy.name.contains(form.search.data) | Galaxy.notes.contains(form.search.data))
        else:
            galaxies = Galaxy.query.all()
        return render_template("/query_results.html", galaxies=galaxies, form = form, form_advanced=form_advanced)

    if request.method == 'GET':
        if form.submit:
            galaxies = Galaxy.query.filter(Galaxy.name.contains(form.search.data) | Galaxy.notes.contains(form.search.data))
        elif form_advanced.submit:
            galaxies = Galaxy.query.filter(Galaxy.name.contains(form_advanced.name.data) | Galaxy.right_ascension.between(form_advanced.right_ascension_min.data, form_advanced.right_ascension_max.data) | Galaxy.declination.between(form_advanced.declination_min.data, form_advanced.declination_max.data) | Galaxy.redshift.between(form_advanced.redshift_min.data, form_advanced.redshift_max.data) | Galaxy.lensing_flag.contains(form_advanced.lensing_flag.data))

    
    return render_template("/query_results.html", form=form, form_advanced=form_advanced, galaxies=galaxies)

    
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
      return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, university = form.university.data, website = form.website.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash ('You have been successfully registered!')
        return redirect(url_for('login'))
    return render_template('./auth/register.html', title= 'Register', form=form)

@app.route("/galaxy_entry_form", methods=['GET', 'POST'])
@login_required
def galaxy_entry_form():
    form = AddGalaxyForm()
    if form.validate_on_submit():
        galaxy = Galaxy(name=form.name.data, right_ascension=form.right_ascension.data, declination = form.declination.data, coordinate_system = form.coordinate_system.data, redshift = form.redshift.data, classification = form.classification.data, lensing_flag = form.lensing_flag.data, notes = form.notes.data)
        db.session.add(galaxy)
        db.session.commit()
        flash ('Galaxy has been added. ')
        return redirect(url_for('main'))
    return render_template('galaxy_entry_form.html', title= 'Galaxy Entry Form', form=form)

@app.route("/line_entry_form", methods=['GET', 'POST'])
@login_required
def line_entry_form():
    form = AddLineForm()
    if form.validate_on_submit():
        line = Line(galaxy_id=form.galaxy_id.data, j_upper=form.j_upper.data, line_id_type = form.line_id_type.data, integrated_line_flux = form.integrated_line_flux.data, integrated_line_flux_uncertainty_positive = form.integrated_line_flux_uncertainty_positive.data, integrated_line_flux_uncertainty_negative = form.integrated_line_flux_uncertainty_negative.data, peak_line_flux = form.peak_line_flux.data, peak_line_flux_uncertainty_positive = form.peak_line_flux_uncertainty_positive.data, peak_line_flux_uncertainty_negative=form.peak_line_flux_uncertainty_negative.data, line_width=form.line_width.data, line_width_uncertainty_positive = form.line_width_uncertainty_positive.data, line_width_uncertainty_negative = form.line_width_uncertainty_negative.data, observed_line_frequency = form.observed_line_frequency.data, observed_line_frequency_uncertainty_positive = form.observed_line_frequency_uncertainty_positive.data, observed_line_frequency_uncertainty_negative = form.observed_line_frequency_uncertainty_negative.data, detection_type = form.detection_type.data, observed_beam_major = form.observed_beam_major.data, observed_beam_minor = form.observed_beam_minor.data, observed_beam_angle = form.observed_beam_angle.data, reference = form.reference.data, notes = form.notes.data)
        db.session.add(line)
        db.session.commit()
        flash ('Line has been added. ')
        return redirect(url_for('main'))
    return render_template('line_entry_form.html', title= 'Line Entry Form', form=form)

@app.route('/galaxy/<name>')
@login_required
def galaxy(name):
    galaxy = Galaxy.query.filter_by(name=name).first_or_404()
    return render_template('galaxy.html', galaxy=galaxy)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
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

@app.route("/submit")
@login_required
def submit():
    return render_template("submit.html")

@app.route("/convert_to_CSV/<table>", methods=['GET', 'POST'])
@login_required
def convert_to_CSV(table):
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
    else:
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

    