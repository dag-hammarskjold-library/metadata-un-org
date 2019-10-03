from flask import render_template, redirect, url_for, request, jsonify, abort, json
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
from metadata import cache
from metadata.unnames import unnames_app
from metadata.unnames.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es, Pagination
from metadata.unnames.utils import get_dataset, get_concept, get_labels, build_breadcrumbs, get_schemes, get_concept_list, make_cache_key
from rdflib import URIRef
import re, requests, urllib

# This should be deprecated/refactored
API = CONFIG.API
INIT = CONFIG.INIT
SINGLE_CLASSES = CONFIG.SINGLE_CLASSES
LANGUAGES = CONFIG.LANGUAGES
KWARGS = CONFIG.KWARGS
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS

# Common set of kwargs to return in all cases. 
return_kwargs = {
    **KWARGS,
    **GLOBAL_KWARGS
}

# Other Init
#ES_CON = Elasticsearch(CONFIG.ELASTICSEARCH_URI)

@unnames_app.route('/')
#@cache.cached(timeout=None, key_prefix=make_cache_key)
def index():
    '''
    This should return a landing page for the unnames application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    #print(cache.get(request.path))

    get_preferred_language(request, return_kwargs)
    this_sc = SINGLE_CLASSES['Root']

    api_path = this_sc['uri']
    return_data = get_dataset(api_path, return_kwargs['lang'])
    print(api_path)

    return render_template('unnames_index.html', data=return_data, **return_kwargs)

@unnames_app.route('/<id>')
#@cache.cached(timeout=None, key_prefix=make_cache_key)
def get_by_id(id):
    '''
    This should return the landing page for a single instance of
    a record, such as an individual Concept, Domain, or MicroThesaurus

    Positive matching is done against a whitelist of RDF Types 
    and id regular expressions patterns as definied in 
    metadata.thesaurus.config. This is intended to pre-screen 
    user input and reject anything that doesn't fit a strict 
    pattern.
    '''
    
    get_preferred_language(request, return_kwargs)

    for single_class in SINGLE_CLASSES:
        this_sc = SINGLE_CLASSES[single_class]
        #print(this_sc)
        p = re.compile(this_sc['id_regex'])
        if p.match(id):
            uri = INIT['uri_base'] + id
            return_data = {'uri':uri, 'properties':[]}
            subtitle = None
            empty = True
            for p in this_sc['get_properties']:
                api_path = '%s%s/propertyValues?resource=%s&property=%s&language=%s' % (
                    API['source'], INIT['thesaurus_pattern'], uri, urllib.parse.quote(p['uri']), return_kwargs['lang']
                )
                got_data = get_dataset(api_path, return_kwargs['lang'])
                
                if len(got_data['values']) > 0:
                    empty = False
                    this_p_v = {'property': p['label'], 'values': got_data['values']}
                    return_data['properties'].append(this_p_v)
                    if p['uri'] == this_sc['label_uri']:
                        subtitle = got_data['values'][0]['label']
            if empty:
                return render_template('404.html', **return_kwargs), 404
            return render_template(this_sc['template'], **return_kwargs, data=return_data, subtitle=subtitle)
        else:
            next
            
    return render_template('404.html', **return_kwargs), 404
