from flask import render_template, redirect, url_for, request, jsonify, abort, json, Response
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
from rdflib import Graph, term, URIRef, Literal, Namespace, RDF
from rdflib.namespace import SKOS
from metadata import cache
from metadata.lib.poolparty import PoolParty, Thesaurus
from metadata.sdg import sdg_app
from metadata.sdg.config import CONFIG
from metadata.sdg.utils import get_or_update
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es, Pagination, make_cache_key
#from metadata.sdg.utils import get_concept, get_labels, build_breadcrumbs, get_schemes, get_concept_list, make_cache_key
from urllib.parse import quote, unquote, unquote_plus
import re, requests



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
    this_c = CONFIG.SINGLE_CLASSES['Root']
    root_concept = get_or_update(this_c['scheme_uri'])

    return_data = {
        'prefLabel': root_concept.pref_label(return_kwargs['lang']),
    }

    goals = []
    for goal_uri in root_concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#hasTopConcept').object:
        goal = get_or_update(goal_uri)
        goal.notes = goal.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
        targets = []
        for target_uri in goal.get_property_by_predicate('http://metadata.un.org/sdg/ontology#hasTarget').object:
            target = get_or_update(target_uri)
            target.notes = target.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
            indicators = []
            for indicator_uri in target.get_property_by_predicate('http://metadata.un.org/sdg/ontology#hasIndicator').object:
                indicator = get_or_update(indicator_uri)
                indicator.notes = indicator.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
                indicators.append(indicator)
            target.indicators = indicators
            targets.append(target)
        goal.targets = targets
        goals.append(goal)
    
    return_data['goals'] = goals

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
                uri = INIT['uri_base'] + id
                display = this_c['display']
                return_data = {}
                
                concept = thesaurus.get_concept(uri, properties=this_c['get_properties'], language=return_kwargs['lang'])

                if this_c['children'] is not None:
                    children_uri = unquote(this_c['children']['uri'])
                    child_accessor = this_c['children']['name']
                    children = []
                
                    for child in concept['properties'][children_uri]:
                        c = thesaurus.get_concept(child, language=return_kwargs['lang'])
                        children.append(c)
                    return_data = { 'concept': concept, this_c['children']['name']: sorted(children, key=lambda k: k['uri']) }
                else:
                    child_accessor = None
                    return_data = { 'concept': concept }

                return render_template(this_c['template'], data=return_data, child_accessor=child_accessor, display=display, **return_kwargs)
        except KeyError:
            next
    abort(404)

@sdg_app.route('/menu')
def menu():
    return render_template('sdg_about.html')

@sdg_app.route('/_expand')
def _expand():
    uri = request.args.get('uri',None)
    lang = request.args.get('lang','en')
    properties = request.args.get('properties',None)

    if uri is not None:
        concept = thesaurus.get_concept(uri, properties=['all'], language=lang)
        return jsonify(concept)
    else:
        abort(400)