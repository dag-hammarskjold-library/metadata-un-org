from flask import render_template, redirect, url_for, request, jsonify
from metadata import app
from metadata import cache
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, write_to_index
from elasticsearch import Elasticsearch
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
    return render_template('index.html', blueprints=blueprints, launched=app.launched, **return_kwargs)
    
@app.route('/feedback')
def feedback():
    '''
    This is a temporary feedback collection tool for the beta release of the site.
    It can be enabled or disabled as necessary during testing phases.
    '''
    get_preferred_language(request, return_kwargs)
    return render_template('feedback.html', **return_kwargs)

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

@app.route('/_reindex', methods=['POST'])
def reindex():
    try:
        body = request.form['body']
    except KeyError:
        return jsonify({'status': 'err_no_body', 'description': 'No document body supplied.'})

    try:
        es_uri = request.form['search_uri']
    except KeyError:
        return jsonify({'status': 'err_no_search_uri', 'description': 'No search URI supplied.'})

    try:
        index_name = request.form['index_name']
    except KeyError:
        return jsonify({'status': 'err_no_index', 'description': 'No index name supplied.'})

    try:
        post_key = request.form['key']
        if post_key == CACHE_KEY:
            es_connection = Elasticsearch(es_uri)
            res = write_to_index(es_connection, index_name, body)
            print(res)
            return jsonify({'status': 'success', 'description': 'The document was reindexed successfully.'})
        else:
            return jsonify({'status': 'err_bad_key', 'description': 'Incorrect post key supplied.'})

    except KeyError:
        return jsonify({'status': 'err_no_key', 'description': 'No post key supplied.'})
