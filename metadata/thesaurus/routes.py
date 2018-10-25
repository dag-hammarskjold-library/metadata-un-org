from flask import render_template, redirect, url_for, request, jsonify, abort
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import LIST_CLASSES, SINGLE_CLASSES, LANGUAGES, KWARGS
from metadata.config import GLOBAL_KWARGS
from metadata.utils import get_preferred_language
import re

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
    return render_template('thesaurus_index.html', **return_kwargs)

@thesaurus_app.route('/browse/<list_class>')
def browse(list_class):
    '''
    This should return the landing page for a listable class of 
    records, such as ConceptSchemes, Domains, etc.
    '''
    get_preferred_language(request, return_kwargs)

    if list_class in LIST_CLASSES:
        this_lc = LIST_CLASSES[list_class]
        return render_template(this_lc['template'], **return_kwargs)
    else:
        abort(403)

@thesaurus_app.route('/<single_class>/<id>')
def single_class(single_class,id):
    '''
    This should return the landing page for a single instance of
    a record, such as an individual Concept.

    Positive matching is done against a whitelist of RDF Types 
    and id regular expressions patterns as definied in 
    metadata.thesaurus.config. This is intended to pre-screen 
    user input and reject anything that doesn't fit a strict 
    pattern.
    '''
    get_preferred_language(request, return_kwargs)
    if single_class in SINGLE_CLASSES:
        this_sc = SINGLE_CLASSES[single_class]
        p = re.compile(this_sc['id_regex'])
        if p.match(id):
            # the pattern matches at least
            return render_template(this_sc['template'], **return_kwargs)
        else:
            abort(403)
    else:
        abort(403)

@thesaurus_app.route('/search')
def search():
    return render_template('search.html', **return_kwargs)