from flask import Flask, jsonify, make_response, render_template
from flask_api import FlaskAPI
import flask
from flask_cors import cross_origin, CORS


app = FlaskAPI(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/login')
def login():
    return render_template("auth/login.html")