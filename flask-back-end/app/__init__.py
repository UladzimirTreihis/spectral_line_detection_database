from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import *
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import math
from sqlalchemy import event
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page'
engine = create_engine('sqlite:///app.db', echo=False, connect_args={"check_same_thread": False})
admin = Admin (template_mode='bootstrap3')

@event.listens_for(engine, 'connect')
def create_math_functions_on_connect(dbapi_connection, connection_record):
    dbapi_connection.create_function('sin', 1, math.sin)
    dbapi_connection.create_function('cos', 1, math.cos)
    dbapi_connection.create_function('acos', 1, math.acos)
    dbapi_connection.create_function('radians', 1, math.radians)

Session = sessionmaker()
Session.configure(bind=engine)

#create the instance of flask app
def create_app(config_class = DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
 
    #configuration 
    #if app.config["ENV"] == "production":
        #app.config.from_object("config.ProductionConfig")
    #elif app.config["ENV"] == "testing":
        #app.config.from_object("config.TestingConfig")
    #else:
        #app.config.from_object("config.DevelopmentConfig")
    
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    admin.init_app(app)
    
    
    engine = create_engine('sqlite:///app.db', echo=False, connect_args={"check_same_thread": False})
    
    Session = sessionmaker()
    Session.configure(bind=engine)

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
            mail_handler = SMTPHandler(mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']), fromaddr='no-reply@' + app.config['MAIL_SERVER'], toaddrs=app.config['ADMINS'], subject='Datavase Failure', credentials=auth, secure=secure) 
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        #Logs files function properly
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







