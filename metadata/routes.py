from flask import render_template, redirect, url_for, request, jsonify
from metadata import app
from metadata import cache
from .config import GLOBAL_CONFIG
from .utils import get_preferred_language
import importlib

LANGUAGES = GLOBAL_CONFIG.LANGUAGES
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS
CACHE_KEY = GLOBAL_CONFIG.CACHE_KEY

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
        this_config = importlib.import_module('.config', package='metadata.' + bp).CONFIG
        blueprints[bp] = this_config.INIT
    return render_template('index.html', blueprints=blueprints, **return_kwargs)
    

@app.route('/_uncache', methods=['POST'])
def uncache(): 
    '''
    This allows the cache to be cleared. It's key controlled, but not
    intended to be otherwise protected with better security.

    The key is defined in metadata.config.CACHE_KEY
    '''
    try:
        post_key = request.form['key']
        print('Got ' + post_key + '...')
        if post_key == CACHE_KEY:
            print('Clearing cache')
            cache.clear()
        else:
            print('But it was invalid.')
    except KeyError:
        print('No key supplied')
        post_key = 'nonce'
    return redirect('/')