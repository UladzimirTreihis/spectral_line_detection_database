from flask import Blueprint
from flask_admin.contrib.sqla import ModelView
from app.models import User, Galaxy, Line
from app import admin, db


bp = Blueprint('adm', __name__)

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Galaxy, db.session))
admin.add_view(ModelView(Line, db.session))