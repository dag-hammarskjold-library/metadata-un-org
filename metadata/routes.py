from flask import render_template, redirect, url_for, request, jsonify
from metadata import app
from .config import LANGUAGES, GLOBAL_KWARGS
from .utils import get_preferred_language
import importlib

return_kwargs = {
    **GLOBAL_KWARGS
}

@app.route('/', methods=['GET'])
def index():
    '''
    This should return a landing page for the base application. 
    The landing page should describe what's here and provide links 
    to the ontologies and schemas collected here.
    '''
    get_preferred_language(request, return_kwargs)
    blueprints = {}
    for bp in app.blueprints:
        blueprints[bp] = importlib.import_module('.config', package='metadata.' + bp).INIT
    return render_template('index.html', blueprints=blueprints, **return_kwargs)