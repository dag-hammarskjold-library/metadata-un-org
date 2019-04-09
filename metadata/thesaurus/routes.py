from flask import render_template, redirect, url_for, request, jsonify, abort, json
from metadata import cache
from metadata.config import API
from metadata.semantic import Term
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import INIT, SINGLE_CLASSES, LANGUAGES, KWARGS
from metadata.config import GLOBAL_KWARGS, GRAPH
from metadata.utils import get_preferred_language
from metadata.thesaurus.utils import get_concept, get_labels, build_breadcrumbs
import re, requests

# Common set of kwargs to return in all cases. 
return_kwargs = {
    **KWARGS,
    **GLOBAL_KWARGS
}

def make_cache_key(*args, **kwargs):
    '''
    Quick function to make cache keys with the full
    path of the request, including search strings
    '''
    path = request.full_path
    return path

@thesaurus_app.route('/')
@cache.cached(timeout=None, key_prefix=make_cache_key)
def index():
    '''
    This should return a landing page for the thesaurus application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    get_preferred_language(request, return_kwargs)
    this_sc = SINGLE_CLASSES['Root']
    uri = this_sc['uri']
    return_properties = ",".join(this_sc['get_properties'])
    api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], uri, return_properties, return_kwargs['lang']
    )

    #print(api_path)
    return_data = get_concept(uri, api_path, this_sc, return_kwargs['lang'])
    #print(return_data)

    return render_template('thesaurus_index.html', data=return_data, **return_kwargs)

@thesaurus_app.route('/<id>')
@cache.cached(timeout=None, key_prefix=make_cache_key)
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
    
    if id == '00':
        return redirect('/')
    get_preferred_language(request, return_kwargs)

    for single_class in SINGLE_CLASSES:
        this_sc = SINGLE_CLASSES[single_class]
        p = re.compile(this_sc['id_regex'])
        if p.match(id):
            uri = INIT['uri_base'] + id
            return_properties = ",".join(this_sc['get_properties'])
            api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
                API['source'], INIT['thesaurus_pattern'], uri, return_properties, return_kwargs['lang']
            )
            #print(api_path)
            return_data = get_concept(uri, api_path, this_sc, return_kwargs['lang'])
            if return_data is None:
                return render_template('404.html', **return_kwargs), 404
            return render_template(this_sc['template'], **return_kwargs, data=return_data)
        else:
            next
            
    return render_template('404.html', **return_kwargs), 404

@thesaurus_app.route('/categories')
#@cache.cached(timeout=None, key_prefix=make_cache_key)
def categories():
    get_preferred_language(request, return_kwargs)
    api_path = '%s%s/schemes?language=%s' % (
        API['source'], INIT['thesaurus_pattern'], return_kwargs['lang']
    )
    
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        jsdata = json.loads(jsresponse.text)
        for jsd in jsdata:
            #this_sc = SINGLE_CLASSES['']
            d_identifier = jsd['uri'].split('/')[-1]
            jsd['identifier'] = d_identifier
            
            # Get the top concepts of each scheme
            #jsdata['childconcepts'] = build_list()
        return_data = sorted(jsdata, key=lambda k: k['uri'])
    else:
        return render_template('404.html', **return_kwargs), 404

    return render_template('thesaurus_categories.html', data=return_data, **return_kwargs)

@thesaurus_app.route('_expand_category')
@cache.cached(timeout=None, key_prefix=make_cache_key)
def _expand_category():
    '''
    This expands a category and is intended to be used asynchronously by several methods. 
    It returns JSON.
    If it's given no request arguments, it assumes Domain as the type and 01 as the value.
    '''
    category = request.args.get('category', '01')
    category_type = request.args.get('type', 'Domain')
    if category_type in SINGLE_CLASSES:
        this_sc = SINGLE_CLASSES[category_type]
        child_accessor = this_sc['child_accessor_property']
        uri = INIT['uri_base'] + category
        api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
            API['source'], INIT['thesaurus_pattern'], uri, child_accessor, return_kwargs['lang']
        )
        #print(api_path)
        return_data = get_concept(uri, api_path, this_sc, return_kwargs['lang'])
        #print(return_data['properties'])

        if category_type == 'Domain':
            print(return_data['properties']['http://www.w3.org/2004/02/skos/core#hasTopConcept'])
            return jsonify(return_data['properties']['http://www.w3.org/2004/02/skos/core#hasTopConcept'])
        else:
            return jsonify(return_data['narrowers'])
    else:
        return render_template('404.html', **return_kwargs), 404

#@thesaurus_app.route('/alphabetical')

#@thesaurus_app.route('/new')

#@thesaurus_app.route('/help')