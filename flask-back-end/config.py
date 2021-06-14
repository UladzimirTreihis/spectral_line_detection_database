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
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
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