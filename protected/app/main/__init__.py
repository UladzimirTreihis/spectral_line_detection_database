from flask import Blueprint
import logging
from config import template_dir

bp = Blueprint('main', __name__, template_folder=template_dir)

logging.basicConfig(filename='main_record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

from app.main import routes