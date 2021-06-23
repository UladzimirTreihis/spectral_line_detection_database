from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User

#log-in route
@bp.route("/login", methods=['GET', 'POST'])
def login():
    #if user is already authenticated, the log-in address redirects to home
    if current_user.is_authenticated: 
      return redirect(url_for('main.home'))
    #form becomes an instance of LoginForm function
    form = LoginForm()
    if form.validate_on_submit():
        #creating local user object
        user = User.query.filter_by(username=form.username.data).first()
        #If user does not exist or username/password incorrect -> redirect to log-in again
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        #If the condition above was false, it logs-in the user and checks the remember me info; redirects to the temporal login_successful page.
        if not is_admin (form.username.data):
            login_user(user, remember=form.remember_me.data)
            #the code for redirection back to @index once logged-in successfully
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.main')
            return redirect(next_page)
        else:
            return redirect (url_for ('admin.index'))
    return render_template("./auth/login.html", title='Sign In', form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
      return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, university = form.university.data, website = form.website.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash ('You have been successfully registered!')
        return redirect(url_for('auth.login'))
    return render_template('./auth/register.html', title= 'Register', form=form)

def is_admin(username):
    if username == "admin":
        return True
