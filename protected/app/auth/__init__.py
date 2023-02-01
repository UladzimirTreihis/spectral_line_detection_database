from flask import Blueprint
from config import template_dir

bp = Blueprint('auth', __name__, template_folder=template_dir +'/auth')

#from app.auth import routes