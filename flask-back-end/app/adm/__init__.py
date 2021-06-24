from flask import Blueprint, url_for, redirect
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose
from flask_admin.model.template import EndpointLinkRowAction
from app.models import User, Galaxy, Line, TempGalaxy, TempLine
from app import admin, db

bp = Blueprint('adm', __name__)

class TempGalaxyView(ModelView):
    column_extra_row_actions = [  # Add a new action button
        EndpointLinkRowAction("glyphicon glyphicon-ok", ".approve_view"),
    ]

    @expose("/approve", methods=("GET",))
    def approve_view(self):
        return redirect (url_for ('tempgalaxy.index_view'))

class TempLineView(ModelView):
    column_extra_row_actions = [  # Add a new action button
        EndpointLinkRowAction("glyphicon glyphicon-ok", ".approve_view"),
    ]

    @expose("/approve", methods=("GET",))
    def approve_view(self):
        return redirect (url_for ('templine.index_view'))

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Galaxy, db.session))
admin.add_view(ModelView(Line, db.session))
admin.add_view(TempGalaxyView (TempGalaxy, db.session))
admin.add_view(TempLineView (TempLine, db.session))

