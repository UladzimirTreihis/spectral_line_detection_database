from flask_login import login_manager
from flask_user import user_manager
from app import create_app
from app.models import db, User, Galaxy, Line, Role
from flask_user import UserManager

app=create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Galaxy': Galaxy, 'Line': Line, 'Role': Role}
