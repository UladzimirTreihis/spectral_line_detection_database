from flask import Blueprint, url_for, redirect, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.actions import action
from app.models import User, Galaxy, Line, TempGalaxy, TempLine
from app import admin, db


bp = Blueprint('adm', __name__)

class TempGalaxyView(ModelView):
    @action('approve', 'Approve')
    def action_approve(self, ids):
        flash ("Approved :) ")
        

class TempLineView(ModelView):
    @action('approve', 'Approve')
    def action_approve(self, ids):
        flash ("Approved :) ")

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Galaxy, db.session))
admin.add_view(ModelView(Line, db.session))
admin.add_view(TempGalaxyView (TempGalaxy, db.session, category = "New Entries"))
admin.add_view(TempLineView(TempLine, db.session, category = "New Entries"))

