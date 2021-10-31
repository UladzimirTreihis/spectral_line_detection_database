import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    #the dir is still /app but database is supposed to be outside with other config files?
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Flask-Mail SMTP server settings
    #MAIL_SERVER = 'smtp.gmail.com'
    #MAIL_PORT = 465
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'line.database.test@gmail.com'
    MAIL_PASSWORD = 'enrjbkfrbkzxboxk'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHEMENTS = False

    # Flask-User settings
    #USER_APP_NAME = "Flask-User Basic App"      # Shown in and email templates and page footers
    #USER_ENABLE_EMAIL = True        # Enable email authentication
    #USER_ENABLE_USERNAME = False    # Disable username authentication
    #USER_EMAIL_SENDER_NAME = USER_APP_NAME
    #USER_EMAIL_SENDER_EMAIL = "noreply@example.com"

    #FLASK-SECURITY
    SECURITY_PASSWORD_SALT = 'dgdfsgdsfghf5hf6'
    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    #SECURITY_LOGIN_USER_TEMPLATE = 'templates'
    SECURITY_REGISTERABLE = True
    SECURITY_SENDREGISTER_EMAIL = False
    SECURITY_CONFIRMABLE = True
    SECURITY_EMAIL_SENDER = 'email@example.com'
    #SECURITY_REGISTER_URL = '/admin/create_account'
#app.config['SECURITY_LOGIN_URL'] = '/admin/login'
#app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
#SECURITY_LOGOUT_URL = '/logout'
#SECURITY_POST_LOGOUT_VIEW = '/home'
#app.config['SECURITY_RESET_URL'] = '/admin/reset'
#app.config['SECURITY_CHANGE_URL'] = '/admin/change'
#app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ['email', 'username']

    ADMINS = ['vtreygis@gmail.com']
    EMITTED_FREQUENCY = {
    1:115.27120180, 
    2:230.53800000, 
    3:345.79598990, 
    4:461.04076820, 
    5:576.26793050,
    6:691.47307630,
    7:806.65180600,
    8:921.79970000,
    9:1036.91239300,
    10:1151.98545200,
    11:1267.01448600,
    12:1381.99510500,
    13:1496.92290900,
    14:1611.79351800,
    15:1726.60250570,
    16:1841.34550600,
    17:1956.01813900,
    18:2070.61599300,
    19:2185.13468000,
    20:2299.56984200,
    21:2413.91711300,
    22:2528.17206000,
    23:2642.33034590,
    24:2756.38758400,
    25:2870.33940700,
    26:2984.18145500,
    27:3097.90936100,
    28:3211.51875060,
    29:3325.00528270,
    30:3438.36461100}

CO = {
    115.27120180:"1", 
    230.53800000:"2", 
    345.79598990:"3", 
    461.04076820:"4", 
    576.26793050:"5",
    691.47307630:"6",
    806.65180600:"7",
    921.79970000:"8",
    1036.91239300:"9",
    1151.98545200:"10",
    1267.01448600:"11",
    1381.99510500:"12",
    1496.92290900:"13",
    1611.79351800:"14",
    1726.60250570:"15",
    1841.34550600:"16",
    1956.01813900:"17",
    2070.61599300:"18",
    2185.13468000:"19",
    2299.56984200:"20",
    2413.91711300:"21",
    2528.17206000:"22",
    2642.33034590:"23",
    2756.38758400:"24",
    2870.33940700:"25",
    2984.18145500:"26",
    3097.90936100:"27",
    3211.51875060:"28",
    3325.00528270:"29",
    3438.36461100:"30"}


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True

EMITTED_FREQUENCY = {
    1:115.27120180, 
    2:230.53800000, 
    3:345.79598990, 
    4:461.04076820, 
    5:576.26793050,
    6:691.47307630,
    7:806.65180600,
    8:921.79970000,
    9:1036.91239300,
    10:1151.98545200,
    11:1267.01448600,
    12:1381.99510500,
    13:1496.92290900,
    14:1611.79351800,
    15:1726.60250570,
    16:1841.34550600,
    17:1956.01813900,
    18:2070.61599300,
    19:2185.13468000,
    20:2299.56984200,
    21:2413.91711300,
    22:2528.17206000,
    23:2642.33034590,
    24:2756.38758400,
    25:2870.33940700,
    26:2984.18145500,
    27:3097.90936100,
    28:3211.51875060,
    29:3325.00528270,
    30:3438.36461100}

COL_NAMES_2 = {
    'name':'Name of the galaxy',
    'right_ascension' : 'Right ascension',
    'declination':'Declination',
    'coordinate_system':'Coordinate System',
    'redshift':'Redshift of the galaxy',
    'lensing_flag':'Lensing flag (l/u)',
    'classification':'Classification',
    'g_notes':'Notes',
    'j_upper':'J_upper',
    'integrated_line_flux':'Integrated line flux',
    'integrated_line_flux_uncertainty_positive':'Integrated line flux positive uncertainty',
    'integrated_line_flux_uncertainty_negative':'Integrated line flux negative uncertainty',
    'peak_line_flux':'Peak line flux',
    'peak_line_flux_uncertainty_positive':'Peak line flux positive uncertainty',
    'peak_line_flux_uncertainty_negative':'Peak line flux negative uncertainty',
    'line_width':'Line width',
    'line_width_uncertainty_positive':'Line width positive uncertainty',
    'line_width_uncertainty_negative':'Line width negative uncertainty',
    'freq_type':'Frequency type (z/f)',
    'observed_line_frequency':'Observed line frequency/redshift',
    'observed_line_frequency_uncertainty_positive':'Observed line frequency/redshift positive uncertainty',
    'observed_line_frequency_uncertainty_negative':'Observed line frequency/redshift negative uncertainty',
    'detection_type':'Detection type (Single Dish/Interferometric)',
    'observed_beam_major':'Observed Beam Major',
    'observed_beam_minor':'Observed Beam Minor',
    'observed_beam_angle':'Observed Beam Angle',
    'reference':'Reference',
    'l_notes':'Notes'
}
COL_NAMES = {
    'name':'name',
    'right_ascension' : 'right_ascension',
    'declination':'declination',
    'coordinate_system':'coordinate_system',
    'redshift':'redshift',
    'lensing_flag':'lensing_flag',
    'classification':'classification',
    'g_notes':'notes',
    'emitted_frequency':'emitted_frequency',
    'species':'species',
    'j_upper':'j_upper',
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
    'observed_line_frequency':'observed_line_frequency',
    'observed_line_frequency_uncertainty_positive':'observed_line_frequency_uncertainty_positive',
    'observed_line_frequency_uncertainty_negative':'observed_line_frequency_uncertainty_negative',
    'detection_type':'detection_type',
    'observed_beam_major':'observed_beam_major',
    'observed_beam_minor':'observed_beam_minor',
    'observed_beam_angle':'observed_beam_angle',
    'reference':'reference',
    'l_notes':'notes'
}

dec_reg_exp = '((([+]+)|([-]+))[0-9][0-9]d[0-5][0-9]m[0-5][0-9][.]*[0-9]*s)|((([+]+)|([-]+))[0-9.]+[.]*[0-9]*)'
ra_reg_exp = '([0-2][0-9]h[0-5][0-9]m[0-5][0-9][.]*[0-9]*s)|([0-9.]+[.]*[0-9]*)'