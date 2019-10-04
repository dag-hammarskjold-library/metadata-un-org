from flask import render_template, redirect, url_for, request, jsonify, abort, json, Response
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
from rdflib import Graph, term, URIRef, Literal, Namespace, RDF
from rdflib.namespace import SKOS
from metadata import cache
from metadata.lib.poolparty import PoolParty, Thesaurus
from metadata.sdg import sdg_app
from metadata.sdg.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es, Pagination
#from metadata.sdg.utils import get_concept, get_labels, build_breadcrumbs, get_schemes, get_concept_list, make_cache_key
from urllib.parse import quote, unquote
import re, requests

pool_party = PoolParty(CONFIG.endpoint, CONFIG.project_id, CONFIG.username, CONFIG.password)
thesaurus = Thesaurus(pool_party)

INIT = CONFIG.INIT
LANGUAGES = CONFIG.LANGUAGES
KWARGS = CONFIG.KWARGS
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS
valid_formats = ['json','ttl', 'xml']

# Common set of kwargs to return in all cases. 
return_kwargs = {
    **KWARGS,
    **GLOBAL_KWARGS
}

@sdg_app.route('/')
def index():
    get_preferred_language(request, return_kwargs)
    return_data = {'scheme':{}, 'children':[]}
    this_c = CONFIG.SINGLE_CLASSES['Root']
    uri = this_c['scheme_uri']
    # Right now, getting this scheme as a concept only works in English. Fixable?
    scheme_data = thesaurus.get_concept(concept=uri)

    if scheme_data is not None:
        return_data['scheme'] = scheme_data
    else:
        abort(404)
    
    scheme_children = getattr(thesaurus, this_c['get_children']['function'])(uri, language=return_kwargs['lang'])
    
    if scheme_children is not None:
        return_data['children'] = sorted(scheme_children, key=lambda k: k['uri'])

    return render_template(this_c['template'], data=return_data, **return_kwargs)

@sdg_app.route('/<id>')
def get_concept(id):
    get_preferred_language(request, return_kwargs)
    return_data = {}
    
    for c in CONFIG.SINGLE_CLASSES:
        this_c = CONFIG.SINGLE_CLASSES[c]
        try:
            p = re.compile(this_c['id_regex'])
            if p.match(id):
                print(c)
                uri = INIT['uri_base'] + id
                display = this_c['display']
                return_data = {}
                
                concept = thesaurus.get_concept(uri, properties=this_c['get_properties'], language=return_kwargs['lang'])

                if this_c['children'] is not None:
                    children_uri = unquote(this_c['children']['uri'])
                    child_accessor = this_c['children']['name']
                    children = []
                
                    for child in concept['properties'][children_uri]:
                        print(child)
                        c = thesaurus.get_concept(child, language=return_kwargs['lang'])
                        children.append(c)
                    return_data = { 'concept': concept, this_c['children']['name']: children }
                else:
                    child_accessor = None
                    return_data = { 'concept': concept }

                #return_data = { 'concept': concept, this_c['children']['name']: children }
                #print(return_data)
                return render_template(this_c['template'], data=return_data, child_accessor=child_accessor, display=display, **return_kwargs)
        except KeyError:
            next
    abort(404)

@sdg_app.route('/menu')
def menu():
    return render_template('sdg_about.html')