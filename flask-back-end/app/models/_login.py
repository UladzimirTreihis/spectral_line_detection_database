from flask_login import LoginManager
from flask_user import UserManager

my_login_manager = LoginManager()
my_user_manager = UserManager(app=None, db=None, UserClass=None)
