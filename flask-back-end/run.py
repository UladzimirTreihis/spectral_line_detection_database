from app import app, db
from app.models import User, Galaxy, Line

if __name__ == "__main__":
    app.run(debug = True, use_reloader = True) 

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Galaxy': Galaxy, 'Line': Line}

from app import routes