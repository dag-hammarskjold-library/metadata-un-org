from flask import render_template, redirect, url_for, request, jsonify
from metadata import app

@app.route('/', methods=['GET'])
def index():
    '''
    This should return a landing page for the base application. 
    The landing page should describe what's here and provide links 
    to the ontologies and schemas collected here.
    '''
    return render_template('index.html')