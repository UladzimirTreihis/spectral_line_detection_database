from flask import Blueprint
from config import template_dir


bp = Blueprint('errors', __name__, template_folder=template_dir+'/errors')

from app.errors import handlers    