from app import app, db
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Galaxy, Line
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AddGalaxyForm, AddLineForm
from werkzeug.urls import url_parse
from datetime import datetime

#The last-seen functionality (if necessary), otherwise it could still be useful of any before_request functionality
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

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

@app.route("/main")
@login_required
def main():
    return render_template("/main.html")

@app.route("/entry_file")
@login_required
def entry_file():
    return render_template("/entry_file.html")

@app.route("/query")
@login_required
def query():
    return render_template("/query.html")
    
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

#route for galaxy/line form submission, the form yet to be developed    
@app.route("/submit")
def submit():
    return render_template("submit.html")