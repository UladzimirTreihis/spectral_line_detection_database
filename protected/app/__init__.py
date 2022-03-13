from re import template
from flask import Flask, request, redirect, url_for
from flask_migrate import Migrate
from flask_security import SQLAlchemyUserDatastore, Security, current_user
from config import *
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import math
from sqlalchemy import event
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from .models import db, User, Role
from datetime import datetime
from flask_security.forms import ConfirmRegisterForm, Required, StringField
from flask_mail import Mail



migrate = Migrate()
mail = Mail()
engine = create_engine('sqlite:///app.db', echo=False, connect_args={"check_same_thread": False})
admin = Admin (template_mode='bootstrap3')

#Flask-Security
class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    username = StringField('Username', [Required()])

#Flask-Admin
class RestrictedAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next = request.url))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()

@event.listens_for(engine, 'connect')
def create_math_functions_on_connect(dbapi_connection, connection_record):
    dbapi_connection.create_function('sin', 1, math.sin)
    dbapi_connection.create_function('cos', 1, math.cos)
    dbapi_connection.create_function('acos', 1, math.acos)
    dbapi_connection.create_function('radians', 1, math.radians)

Session = sessionmaker()
Session.configure(bind=engine)

logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


#create the instance of flask app
def create_app(config_class = DevelopmentConfig):
    template_dir = '../../public/templates'
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(config_class)
 
    #configuration 
    #if app.config["ENV"] == "production":
        #app.config.from_object("config.ProductionConfig")
    #elif app.config["ENV"] == "testing":
        #app.config.from_object("config.TestingConfig")
    #else:
        #app.config.from_object("config.DevelopmentConfig")
    
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    mail.init_app(app)
    admin.init_app(app, index_view=RestrictedAdminIndexView(name='Index'), url='/')
    app.jinja_env.filters['zip'] = zip

    engine = create_engine('sqlite:///app.db', echo=False, connect_args={"check_same_thread": False})
    Session = sessionmaker()
    Session.configure(bind=engine)

    

    #Flask-Security

    security.init_app(app, user_datastore, confirm_register_form=ExtendedConfirmRegisterForm)

    # Create all database tables
    with app.app_context():
        db.create_all()

        #Flask-Mail
        #mail.send_message('New test message from Ulad',
        #          sender="line.database.test@gmail.com",
        #          recipients=['line.database.test@gmail.com'],
        #          body="The app has been initiated")

        # Create 'member@example.com' user with no roles
        if not User.query.filter(User.email == 'member@example.com').first():
            user = user_datastore.create_user(email='member@example.com', password = 'member', username='member', confirmed_at=datetime.now())
            
            db.session.add(user)
            db.session.commit()

        # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
        if not User.query.filter(User.email == 'admin@example.com').first():
            admin_role = user_datastore.create_role(name='admin')
            user = user_datastore.create_user(email='admin@example.com', password='admin', username='admin', confirmed_at=datetime.now())
            user_datastore.add_role_to_user(user, admin_role)
            db.session.add(admin_role)
            db.session.add(user)
            db.session.commit()

            
            #user.roles.append(Role(name='Admin'))
            #user.roles.append(Role(name='Agent'))


    #BluePrints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    from app.adm import bp as adm_bp
    app.register_blueprint(adm_bp)

    UPLOAD_FOLDER = 'static/files'
    app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

    if not app.debug:
        #The email configuration for errors does not work yet on external mails such as gmail.com. works only internally on imaginary email servise on a separate localhost. 
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure()
            mail_handler = SMTPHandler(mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']), fromaddr='no-reply@' + app.config['MAIL_SERVER'], toaddrs=app.config['ADMINS'], subject='Database Failure', credentials=auth, secure=secure) 
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        #Logs files function properly

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/database.log', maxBytes=10240, backupCount=10)
            formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('App startup')
    
    return app

#the conn
@event.listens_for(engine, 'connect')
def create_math_functions_on_connect(dbapi_connection, connection_record):
        dbapi_connection.create_function('sin', 1, math.sin)
        dbapi_connection.create_function('cos', 1, math.cos)
        dbapi_connection.create_function('acos', 1, math.acos)
        dbapi_connection.create_function('radians', 1, math.radians)







