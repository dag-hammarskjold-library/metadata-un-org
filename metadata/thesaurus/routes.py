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

@thesaurus_app.route('/')
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

    return_data = get_concept(uri, api_path, this_sc)

    return render_template('thesaurus_index.html', data=return_data, **return_kwargs)

@thesaurus_app.route('/<id>')
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
            print(api_path)
            return_data = get_concept(uri, api_path, this_sc, return_kwargs['lang'])
            if return_data is None:
                return render_template('404.html', **return_kwargs), 404
            return render_template(this_sc['template'], **return_kwargs, data=return_data)
        else:
            next
            
    return render_template('404.html', **return_kwargs), 404

@thesaurus_app.route('_get_property')
def get_property():
    '''
    This loads a referenceable property, generally a list of things like labels
    and child concepts. Always returns JSON. Can be used by AJAX in templates.
    '''

    return jsonify('foo')

#@thesaurus_app.route('/categories')

#@thesaurus_app.route('/alphabetical')

#@thesaurus_app.route('/new')

#@thesaurus_app.route('/help')