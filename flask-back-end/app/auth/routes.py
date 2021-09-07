from flask import render_template, redirect, url_for, flash, request
from flask.helpers import get_load_dotenv
from sqlalchemy.orm import session
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user
from flask_user import current_user, login_required, roles_required
from app import db, Session
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User, UserRoles, Role, my_login_manager


#function that will provide a user to the flask-login, given the user's ID
@my_login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
#log-in route
@bp.route("/login", methods=['GET', 'POST'])
def login():
    session=Session()
    #if user is already authenticated, the log-in address redirects to home
    if current_user.is_authenticated: 
      return redirect(url_for('main.home'))
    #form becomes an instance of LoginForm function
    form = LoginForm()
    if form.validate_on_submit():
        #creating local user object
        user = User.query.filter_by(username=form.username.data).first()
        #If user does not exist or username/password incorrect -> redirect to log-in again
        if user is None:
            flash('Invalid username')
            return redirect(url_for('auth.login'))
        if user:
            
            authenticated_user = user.check_password(form.password.data)
            if authenticated_user:
                
                user_id = user.id
                
                q_role_id = session.query(UserRoles.role_id).filter(UserRoles.user_id == user_id).first()
                q_role_id_str = str(q_role_id)
                q_role_id_str=q_role_id_str[1:q_role_id_str.find(',')]
                
                q_role_name = session.query(Role.name).filter(Role.id == q_role_id_str).first()
                q_role_name_str = str(q_role_name)
                q_role_name_str=q_role_name_str[2:q_role_name_str.find(',')-1]
             
                if q_role_name_str != 'Admin':
                    login_user(user, remember=form.remember_me.data)
                    #the code for redirection back to @index once logged-in successfully
                    #next_page = request.args.get('next')
                    #if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('main.home')
                    return redirect(next_page)
                else:
                    login_user(user, remember=form.remember_me.data)
                    return redirect (url_for ('admin.index'))
            else:
                flash('Invalid password')
                return redirect(url_for('auth.login'))
        #If the condition above was false, it logs-in the user and checks the remember me info; redirects to the temporal login_successful page.

    return render_template("./auth/login.html", title='Sign In', form=form)


@bp.route("/logout")
#@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@bp.route("/register", methods=['GET', 'POST'])
def register():
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
