from app import app, db
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.forms import RegistrationForm
from werkzeug.urls import url_parse

#default route
@app.route("/")
@app.route("/home")
@login_required
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
            next_page = url_for('home')
        return redirect(next_page)
    return render_template("./auth/login.html", title='Sign In', form=form)

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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash ('You have been succefully registered!')
        return redirect(url_for('login'))
    return render_template('./auth/register.html', title= 'Register', form=form)

#temporal log-in redirection route
@app.route("/login_successful")
def login_successful():
    return render_template("./auth/login_successful.html")

#route for galaxy/line form submission, the form yet to be developed    
@app.route("/submit")
def submit():
    return render_template("submit.html")