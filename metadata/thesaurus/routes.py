from flask import render_template, redirect, url_for, request, jsonify, abort
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import LIST_CLASSES, SINGLE_CLASSES

@thesaurus_app.route('/', methods=['GET'])
def index():
    '''
    This should return a landing page for the thesaurus application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    return render_template('thesaurus_index.html', aspects=LIST_CLASSES)

@thesaurus_app.route('/<list_class>')
def list_class(list_class):
    '''
    This should return the landing page for a listable class of 
    records, such as ConceptSchemes, Domains, etc.
    '''
    if list_class in LIST_CLASSES:
        this_lc = LIST_CLASSES[list_class]
        return render_template(this_lc['template'])
    else:
        abort(403)

@thesaurus_app.route('/<single_class>/<id>')
def single_class(single_class,id):
    '''
    This should return the landing page for a single instance of
    a record, such as an individual Concept
    '''
    return render_template('term.html')