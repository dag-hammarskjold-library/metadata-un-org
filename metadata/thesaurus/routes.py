from flask import render_template, redirect, url_for, request, jsonify, abort, json, Response
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
from rdflib import Graph, term, URIRef, Literal, Namespace, RDF
from rdflib.namespace import SKOS
from metadata import cache
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es, Pagination
from bson.json_util import dumps
#from metadata.thesaurus.utils import get_concept, get_labels, build_breadcrumbs, get_schemes, get_concept_list, make_cache_key
from urllib.parse import quote
from mongoengine import connect
from metadata.lib.ppmdb import Concept, Label, Relationship, reload_concept
from metadata.lib.poolparty import PoolParty, Thesaurus
import re, requests, ssl

# This should be deprecated/refactored
INIT = CONFIG.INIT
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS
valid_formats = ['json','ttl', 'xml']

#mongo_client = MongoClient(CONFIG.connect_string, ssl_cert_reqs=ssl.CERT_NONE)
#db = mongo_client['undhl-issu']
connect(host=CONFIG.connect_string, db='undhl-issu', ssl_cert_reqs=ssl.CERT_NONE)

pool_party = PoolParty(CONFIG.endpoint, CONFIG.project_id, CONFIG.username, CONFIG.password)
thesaurus = Thesaurus(pool_party)

# Common set of kwargs to return in all cases. 
return_kwargs = {
    #**KWARGS,
    **GLOBAL_KWARGS
}
return_kwargs['valid_formats'] = valid_formats

def get_match_class_by_regex(match_classes, pattern):
    return(next(filter(lambda m: re.compile(m['id_regex']).match(pattern),match_classes), None))

def get_match_class_by_name(match_classes, name):
    return(next(filter(lambda m: m['name'] == name ,match_classes), None))


@thesaurus_app.route('/')
def index():
    '''
    This should return a landing page for the thesaurus application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    get_preferred_language(request, return_kwargs)
    root_uri = INIT['uri_base'][:-1]

    return_data = {}

    concept = Concept.objects.get(uri=root_uri)
    return_data['URI'] = concept.uri
    return_data['pref_label'] = concept.pref_label(return_kwargs['lang'])

    this_concept_schemes = []
    for cs in concept.get_property_values_by_predicate('http://purl.org/dc/terms#hasPart'):
        this_data = {}
        this_cs = Concept.objects.get(uri=cs['value'])
        this_data['uri'] = this_cs.uri
        this_data['pref_label'] = this_cs.pref_label(return_kwargs['lang'])
        this_data['identifier'] = this_cs.get_property_by_predicate('http://purl.org/dc/elements/1.1/identifier').object['value']
        this_concept_schemes.append(this_data)
    return_data['Concept Schemes'] = sorted(this_concept_schemes, key=lambda x: x['identifier'])

    this_language_equivalents = []
    for lang in CONFIG.available_languages:
        this_language_equivalents.append(next(filter(lambda x: x.language == lang, concept.pref_labels),None))
    return_data['Language Equivalents'] = this_language_equivalents

    version = concept.get_property_by_predicate('http://purl.org/dc/terms#hasVersion')
    return_data['Version'] = version.object['value']
    

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
    
    get_preferred_language(request, return_kwargs)
    
    this_c = get_match_class_by_regex(CONFIG.match_classes,id)
    if this_c is not None:
        this_uri = CONFIG.INIT['uri_base'] + id
        return_data = {}
        concept = Concept.objects.get(uri=this_uri)
        return_data['URI'] = concept.uri
        return_data['Preferred Term'] = concept.pref_label(return_kwargs['lang'])
        
        this_language_equivalents = []
        for lang in CONFIG.available_languages:
            this_language_equivalents.append(next(filter(lambda x: x.language == lang, concept.pref_labels),None))
        return_data['Language Equivalents'] = this_language_equivalents

        for child_def in this_c['children']:
            this_child_data = []
            for child in concept.get_property_values_by_predicate(child_def['uri']):
                this_data = {}
                this_child = Concept.objects.get(uri=child['value'])
                this_data['uri'] = this_child.uri
                this_data['pref_label'] = this_child.pref_label(return_kwargs['lang'])
                for name,uri in child_def['attributes']:
                    print(name,uri)
                    this_data[name] = this_child.get_property_by_predicate(uri).object['value']
                this_child_data.append(this_data)
            
            if child_def['sort'] is not None:
                return_data[child_def['name']] = sorted(this_child_data, key=lambda x: x[child_def['sort']])
            else:
                return_data[child_def['name']] = sorted(this_child_data, key=lambda x: x['pref_label'].label)
        '''        
        this_breadcrumb_data = []
        for bc in concept.get_property_values_by_predicate(this_c['breadcrumb']['parent']['uri']):
            
            for 
        '''
        print(return_data)


        return render_template(this_c['template'], data=return_data, **return_kwargs)
    else:
        return render_template('404.html', **return_kwargs), 404
 
@thesaurus_app.route('/categories')
def categories():
     pass

@thesaurus_app.route('/alphabetical')
def alphabetical(page):
    pass

@thesaurus_app.route('/new')
def term_updates():
    pass

@thesaurus_app.route('/about')
def about():
    pass

@thesaurus_app.route('/reload', methods=['POST'])
def reload():
    key = request.form.get('key',None)
    uri = request.form.get('uri', None)
    if uri is None:
        return jsonify({'Status': 'Error: uri is required.'})
    if key is None:
        return jsonify({'Status': 'Error: key is required.'})

    if key == GLOBAL_CONFIG.CACHE_KEY:
        #got_concept = thesaurus.get_concept(uri, properties=['all'])
        try:
            reload_concept(uri, thesaurus)
        except:
            return jsonify({'Status': 'Error: Either the operation timed out, or the concept was not found.'})
        return jsonify({'Status':'Success'})
    else:
        return render_template('404.html', **return_kwargs), 404