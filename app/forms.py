from app import app
from flask import render_template

@app.route("/")
def login():
    return render_template("./auth/login.html")

@app.route("/home")
def home():
    return "home"