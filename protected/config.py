import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))
template_dir = '../../../public/templates'

with open('../conf/config.json') as config_file:
    config_file = json.load(config_file)


class Config(object):
    DEBUG = False
    TESTING = False
    #the dir is still /app but database is supposed to be outside with other config files?
    SQLALCHEMY_DATABASE_URI = config_file.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, '../tmp/app.db')
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
     #   'postgres://', 'postgresql://') or \
      #  'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = config_file.get('SECRET_KEY') or 'you-will-never-guess'
    
    # For Postgresql
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') 
    # Flask-Mail SMTP server settings
    #MAIL_SERVER = 'smtp.gmail.com'
    #MAIL_PORT = 465
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = os.environ.get('MAIL_PORT') or 465
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') or True
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or False
    MAIL_USERNAME = config_file.get('MAIL_USERNAME') or 'line.database.test@gmail.com'
    MAIL_PASSWORD = config_file.get('MAIL_PASSWORD') or 'enrjbkfrbkzxboxk'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
    MAIL_MAX_EMAILS = os.environ.get('MAIL_MAX_EMAILS') or None
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND') or False
    MAIL_ASCII_ATTACHEMENTS = os.environ.get('MAIL_ASCII_ATTACHEMENTS') or False

    # Flask-User settings
    #USER_APP_NAME = "Flask-User Basic App"      # Shown in and email templates and page footers
    #USER_ENABLE_EMAIL = True        # Enable email authentication
    #USER_ENABLE_USERNAME = False    # Disable username authentication
    #USER_EMAIL_SENDER_NAME = USER_APP_NAME
    #USER_EMAIL_SENDER_EMAIL = "noreply@example.com"

    #FLASK-SECURITY
    SECURITY_PASSWORD_SALT = config_file.get('SECURITY_PASSWORD_SALT') or 'dgdfsgdsfghf5hf6'
    SECURITY_PASSWORD_HASH = config_file.get('SECURITY_PASSWORD_HASH') or 'sha512_crypt'
    #SECURITY_LOGIN_USER_TEMPLATE = 'templates'
    SECURITY_REGISTERABLE = os.environ.get('SECURITY_REGISTERABLE') or True
    SECURITY_SENDREGISTER_EMAIL = os.environ.get('SECURITY_SENDREGISTER_EMAIL') or False
    SECURITY_CONFIRMABLE = os.environ.get('SECURITY_CONFIRMABLE') or True
    SECURITY_EMAIL_SENDER = os.environ.get('SECURITY_EMAIL_SENDER') or 'email@example.com'
    #SECURITY_REGISTER_URL = '/admin/create_account'
#app.config['SECURITY_LOGIN_URL'] = '/admin/login'
#app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
#SECURITY_LOGOUT_URL = '/logout'
#SECURITY_POST_LOGOUT_VIEW = '/home'
#app.config['SECURITY_RESET_URL'] = '/admin/reset'
#app.config['SECURITY_CHANGE_URL'] = '/admin/change'
#app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ['email', 'username']

    ADMINS = ['line.database.test@gmail.com']


class ProductionConfig(Config):
    SECRET_KEY = config_file.get('SECRET_KEY')
    MAIL_USERNAME = config_file.get('MAIL_USERNAME')
    MAIL_PASSWORD = config_file.get('MAIL_PASSWORD')
    SECURITY_PASSWORD_SALT = config_file.get('SECURITY_PASSWORD_SALT')
    SECURITY_PASSWORD_HASH = config_file.get('SECURITY_PASSWORD_HASH')



class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


COL_NAMES = {
    'name':'name',
    'right_ascension' : 'right_ascension',
    'declination':'declination',
    'right_ascension_weighted_average': 'right_ascension_weighted_average',
    'declination_weighted_average': 'declination_weighted_average',
    'coordinate_system':'coordinate_system',
    'redshift': 'Redshift of the galaxy',
    'lensing_flag':'lensing_flag',
    'classification':'classification',
    'g_notes':'g_notes',
    'emitted_frequency':'emitted_frequency',
    'species':'species',
    'integrated_line_flux':'integrated_line_flux',
    'integrated_line_flux_uncertainty_positive':'integrated_line_flux_uncertainty_positive',
    'integrated_line_flux_uncertainty_negative':'integrated_line_flux_uncertainty_negative',
    'peak_line_flux':'peak_line_flux',
    'peak_line_flux_uncertainty_positive':'peak_line_flux_uncertainty_positive',
    'peak_line_flux_uncertainty_negative':'peak_line_flux_uncertainty_negative',
    'line_width':'line_width',
    'line_width_uncertainty_positive':'line_width_uncertainty_positive',
    'line_width_uncertainty_negative':'line_width_uncertainty_negative',
    'freq_type':'freq_type',
    'observed_line_redshift':'observed_line_redshift',
    'observed_line_redshift_uncertainty_positive':'observed_line_redshift_uncertainty_positive',
    'observed_line_redshift_uncertainty_negative':'observed_line_redshift_uncertainty_negative',
    'detection_type':'detection_type',
    'observed_beam_major':'observed_beam_major',
    'observed_beam_minor':'observed_beam_minor',
    'observed_beam_angle':'observed_beam_angle',
    'reference':'reference',
    'l_notes':'l_notes'
}


def remove_key(d, *keys):
    r = dict(d)
    for key in keys:
        del r[key]
    return r


COL_NAMES_FOR_SUBMISSION = remove_key(
    COL_NAMES,
    'redshift',
    'right_ascension_weighted_average',
    'declination_weighted_average'
)

dec_reg_exp = '((([+]+)|([-]+))[0-9][0-9]d[0-5][0-9]m[0-5][0-9][.]*[0-9]*s)|((([+]+)|([-]+))[0-9.]+[.]*[0-9]*)'
ra_reg_exp = '([0-2][0-9]h[0-5][0-9]m[0-5][0-9][.]*[0-9]*s)|([0-9.]+[.]*[0-9]*)'
