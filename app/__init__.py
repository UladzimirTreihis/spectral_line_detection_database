from flask import Flask, jsonify, make_response
from flask_api import FlaskAPI
import flask
from flask_cors import cross_origin, CORS


app = FlaskAPI(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]


@app.route('/testapi', methods=['GET'])
@cross_origin()
def example():
    response = make_response( jsonify({'tasks': tasks}))
    return response