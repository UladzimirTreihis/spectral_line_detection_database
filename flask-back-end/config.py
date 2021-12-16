import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    #the dir is still /app but database is supposed to be outside with other config files?
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        #'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # For Postgresql
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') 
    # Flask-Mail SMTP server settings
    #MAIL_SERVER = 'smtp.gmail.com'
    #MAIL_PORT = 465
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = os.environ.get('MAIL_PORT') or 465
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') or True
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'line.database.test@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'enrjbkfrbkzxboxk'
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
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'dgdfsgdsfghf5hf6'
    SECURITY_PASSWORD_HASH = os.environ.get('SECURITY_PASSWORD_HASH') or 'sha512_crypt'
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

CO_f = {
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

C17O_f = {

    224.7135334:"2", 
    337.0605132:"3", 
    449.3947106:"4", 
    561.7121394:"5",
    674.0086961:"6",
    786.2801708:"7",
    898.5223726:"8",
    1010.7311168:"9",
    1151.98545200:"10",
    1235.0315072:"11",
    1347.1147951:"12",

    1571.1266544:"14",

    1794.9043655:"16",
    1906.694987:"17",
    2018.414379:"18",
    2130.058489:"19",
    2241.623136:"20",
    2353.104137:"21",
    2464.497311:"22",
    2575.798474:"23",
    2687.003446:"24",
    2798.108043:"25",
    2909.108084:"26",
    3019.999385:"27",
    3130.777765:"28",
    3241.439042:"29"}

C18O_f = {
    109.7821734:"1", 
    219.5603541:"2", 
    329.3305453:"3", 
    439.0887631:"4", 
    548.8309775:"5",
    658.5532728:"6",
    768.251589:"7",
    877.921954:"8",
    987.560375:"9",
    1097.162865:"10",
    1206.725436:"11",
    1316.244099:"12",

    
    
    
    
    1972.21087:"18",
    2081.3106385:"19",
    2190.3346365:"20",
    2299.2788998:"21",
    2408.1394565:"22",
    2516.9123372:"23",
    2625.5935745:"24",
    2734.1792037:"25",
    2842.6652625:"26",
    2951.047791:"27"}

THIRTEEN_CO_f = {

}

CF_f = {

}

CF_PLUS_f = {

}

CCH_f = {

}

CH_PLUS_f = {

}

CH2_P1_SLASH_2_f = {

}

CH2_P3_SLASH_2_f = {

}

CI_BRACKET_C_HYPHEN_atom_BRACKET_f = {

}

CII_f = {

}

CN_MINUS_f = {

}

CN_f = {

}

CS_f = {

}

Ha_f = {

}

H2O_f = {

}

o_HYPHEN_H2O_PLUS_f = {

}

p_HYPHEN_H2O_PLUS_f = {

}

HCN_f = {

}

HNC_f = {

}

HCO_PLUS_f = {

}

HF_f = {

}

LiH_f = {

}

N2H_PLUS_f = {

}

NH3_f = {

}

NII_BRACKET_N_PLUS_HYPHEN_atom_BRACKET_f = {

}

NO_f = {

}

NO_PLUS_f = {

}

OI_f = {

}

OIII_f = {

}

OH_PLUS_f = {

}

OH_f = {

}

PN_f = {

}

SiC_f = {

}

SiN_f = {

}

SiO_f = {

}

SO2_f = {
    
}

CarbonMonoxide = {"CO": CO_f, "C17O": C17O_f, "C18O": C18O_f, "13CO": THIRTEEN_CO_f}
THIRTEEN_CO = {"13CO": "13CO", "13COv=0": "13CO"}
C17O = {"C17O": "C17O"}
C18O = {"C18O": "C18O"}
CO = {"CO": "CO", "COv=0": "CO", "12CO": "CO", "12C16O": "CO"}

Fluoromethylidyne_Fluoromethyliumylidene = {"CF": CF_f, "CF+": CF_PLUS_f}
CF = {"CF": "CF"}
CF_PLUS = {"CF+": "CF+", "CF+v=0": "CF+"}

Ethynyl_Methylidynium_Mathylidyne = {"CCH": CCH_f, "CH+": CH_PLUS_f, "CH2_P1/2": CH2_P1_SLASH_2_f, "CH2_P3/2": CH2_P3_SLASH_2_f}
CCH = {"CCH": "CCH", "CCHv=0": "CCH", "C2H": "CCH"}
CH_PLUS = {"CH+": "CH+"}
CH2_P1_SLASH_2 = {"CH2_P1/2": "CH2_P1/2"} 
CH2_P3_SLASH_2 = {"CH2_P3/2": "CH2_P3/2"} 

AtomicCarbon_IonisedCarbon = {"CI(C-atom)": CI_BRACKET_C_HYPHEN_atom_BRACKET_f, "CII": CII_f}
CI_BRACKET_C_HYPHEN_atom_BRACKET = {"CI(C-atom)": "CI(C-atom)", "C": "CI(C-atom)", "Ci": "CI(C-atom)", "CI": "CI(C-atom)"}
CII = {"CII": "CII", "C+": "CII"}

CyanideAnion_CyanideRadical = {"CN-": CN_MINUS_f, "CN": CN_f}
CN_MINUS = {"CN-": "CN-"}
CN = {"CN": "CN", "CNv=0": "CN"}

CarbonMonosulfide = {"CS": CS_f}
CS = {"CS": "CS", "CSv=0": "CS"}

HydrogenRecombinationLine = {"Ha": Ha_f}
Ha = {"Ha": "Ha", "Halpha": "Ha", "Hα": "Ha"}

Water_orthoOxidaniumyl_paraOxidaniumyl = {"H2O": H2O_f, "o-H2O+": o_HYPHEN_H2O_PLUS_f, "p-H2O+": p_HYPHEN_H2O_PLUS_f}
H2O = {"H2O": "H2O", "H2Ov=0": "H2O"}
o_HYPHEN_H2O_PLUS = {"o-H2O+": "o-H2O+"}
p_HYPHEN_H2O_PLUS = {"p-H2O+": "p-H2O+"}

HydrogenCyanide_HydrogenIsocyanide = {"HCN": HCN_f, "HNC": HNC_f}
HCN = {"HCN": "HCN", "HCNv=0": "HCN"}
HNC = {"HNC": "HNC", "HNCv=0": "HNC"}

Formylium = {"HCO+": HCO_PLUS_f}
HCO_PLUS = {"HCO+": "HCO+", "HCO+v=0": "HCO+"}

HydrogenFluoride = {"HF": HF_f}
HF = {"HF": "HF"}

LithiumHydride = {"LiH": LiH_f}
LiH = {"LiH": "LiH", "LiHv=0": "LiH"}

Diazenylium = {"N2H+": N2H_PLUS_f}
N2H_PLUS = {"N2H+": "N2H+", "N2H+v=0": "N2H+"}

Ammonia = {"NH3": NH3_f}
NH3 = {"NH3": "NH3", "NH3v=0": "NH3"}

AtomicNitrogen = {"NII(N+-atom)": NII_BRACKET_N_PLUS_HYPHEN_atom_BRACKET_f}
NII_BRACKET_N_PLUS_HYPHEN_atom_BRACKET = {"NII(N+-atom)": "NII(N+-atom)", "N+": "NII(N+-atom)", "Nii": "NII(N+-atom)"}

NitricOxide_NitricOxideIon = {"NO": NO_f, "NO+": NO_PLUS_f}
NO = {"NO": "NO"}
NO_PLUS = {"NO+": "NO+"}

Oxygen_IonisedOxygen = {"OI": OI_f, "OIII": OIII_f}
OI = {"OI": "OI", "O": "OI"} 
OIII = {"OIII": "OIII", "O++": "OIII"}

Hydroxyl = {"OH+": OH_PLUS_f, "OH": OH_f}
OH_PLUS = {"OH+": "OH+"}
OH = {"OH": "OH", "OHv=0": "OH"}

PhosphorousNitride = {"PN": PN_f}
PN = {"PN": "PN", "PNv=0": "PN"}

SiliconMonocarbide = {"SiC": SiC_f}
SiC = {"SiC": "SiC", "SiCv=0": "SiC"}

SiliconMononitride = {"SiN": SiN_f}
SiN = {"SiN": "SiN"}

SiliconMonoxide = {"SiO": SiO_f}
SiO = {"SiO": "SiO", "SiOv=0": "SiO"}

SulfurDioxide = {"SO2": SO2_f}
SO2 = {"SO2": "SO2", "SO2v=0": "SO2"}


