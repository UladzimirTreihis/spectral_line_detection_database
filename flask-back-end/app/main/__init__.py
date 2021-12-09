from flask import Blueprint
import logging

bp = Blueprint('main', __name__)

logging.basicConfig(filename='main_record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

from app.main import routes