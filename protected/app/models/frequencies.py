from ._db import db

class Freq(db.Model):
    __tablename__ = 'freq'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(64))
    chemical_name = db.Column(db.String(64))
    frequency = db.Column(db.Float(32))
    qn = db.Column(db.String(64))