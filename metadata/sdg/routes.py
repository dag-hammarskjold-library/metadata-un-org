from flask import render_template, redirect, url_for, request, jsonify, abort, json, Response
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
from rdflib import Graph, term, URIRef, Literal, Namespace, RDF
from rdflib.namespace import SKOS
from metadata import cache
from metadata.lib.poolparty import PoolParty, Thesaurus
from metadata.sdg import sdg_app
from metadata.sdg.config import CONFIG
from metadata.sdg.utils import get_or_update, replace_concept
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

def get_match_class_by_regex(match_classes, pattern):
    return(next(filter(lambda m: re.compile(m['id_regex']).match(pattern),match_classes), None))

def get_match_class_by_name(match_classes, name):
    return(next(filter(lambda m: m['name'] == name ,match_classes), None))

@sdg_app.route('/')
def index():
    get_preferred_language(request, return_kwargs)
    this_c = get_match_class_by_name(CONFIG.match_classes,'Root')
    root_concept = get_or_update(this_c['scheme_uri'])

    return_data = {
        'prefLabel': root_concept.pref_label(return_kwargs['lang']),
    }

    goals = []
    for goal_uri in root_concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#hasTopConcept').object:
        goal = get_or_update(goal_uri['uri'])
        notes = goal.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
        goal.note = next(filter(lambda x: x['language'] == return_kwargs['lang'],notes),None)
        targets = []
        for target_uri in goal.get_property_by_predicate('http://metadata.un.org/sdg/ontology#hasTarget').object:
            target = get_or_update(target_uri['uri'])
            notes = target.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
            target.note = next(filter(lambda x: x['language'] == return_kwargs['lang'],notes),None)
            notations = target.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#notation').object
            target.notation = next(filter(lambda x: len(x['label']) == 5,notations),None)
            indicators = []
            for indicator_uri in target.get_property_by_predicate('http://metadata.un.org/sdg/ontology#hasIndicator').object:
                indicator = get_or_update(indicator_uri['uri'])
                notes = indicator.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
                indicator.note = next(filter(lambda x: x['language'] == return_kwargs['lang'],notes),None)
                notations = indicator.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#notation').object
                indicator.notation = next(filter(lambda x: len(x['label']) == 8,notations),None)
                indicators.append(indicator)
            target.indicators = sorted(indicators, key=lambda x: x.notation['label'])
            targets.append(target)
        goal.targets = sorted(targets, key=lambda x: x.notation['label'])
        goals.append(goal)
    
    return_data['goals'] = goals

    return render_template(this_c['template'], data=return_data, **return_kwargs)


@sdg_app.route('/<id>', methods=['GET','POST'])
def get_concept(id):
    uri = INIT['uri_base'] + id
    if request.method == 'POST':
        cache_key = request.form.get('cache_key',None)
        if cache_key == GLOBAL_CONFIG.CACHE_KEY:
            res = replace_concept(uri)
            if res:
                return redirect(url_for('sdg.get_concept', id=id))
            else:
                return jsonify({"status":"error"})
        else:
            abort(403)
    else:
        get_preferred_language(request, return_kwargs)
        return_data = {}
        
        this_c = get_match_class_by_regex(CONFIG.match_classes,id)
        if this_c is not None:
            concept = get_or_update(uri)
            return_data = {
                'URI': concept.uri,
                'skos:prefLabel': concept.pref_label(return_kwargs['lang']).label
            }
            if len(concept.alt_labels) > 0:
                return_data['skos:altLabel'] = [x.label for x in concept.alt_labels]
            
            notes = concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
            note = next(filter(lambda x: x['language'] == return_kwargs['lang'], notes),None)
            if note is not None:
                return_data['skos:note'] = note['label']

            in_schemes = concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#inScheme').object
            return_data['skos:inScheme'] = in_schemes

            try:
                broaders = concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#broader').object
                return_data['skos:broader'] = broaders
            except AttributeError:
                pass

            if this_c['children'] is not None:
                child_accessor = this_c['children']['name']
                this_children = []
                for child_uri in concept.get_property_by_predicate(this_c['children']['uri']).object:
                    child = get_or_update(child_uri['uri'])
                    sort_key, attr, sort_length = this_c['children']['sort_children_by']
                    print(child.uri)
                    print(sort_key, attr, sort_length)
                    sort_key_values = child.get_property_by_predicate(sort_key)
                    print(sort_key_values)
                    return_child = {
                        'uri': child.uri,
                        'pref_label': child.pref_label(return_kwargs['lang']),
                        'sort_key': next(filter(lambda x: len(x[attr]) == sort_length, child.get_property_by_predicate(sort_key).object),None)
                    }
                    this_children.append(return_child)
                    
                return_data[this_c['children']['name']] = sorted(this_children, key=lambda x: x['sort_key']['label'])
            else:
                child_accessor = None
            #except:
            #    abort(404)

            return render_template(this_c['template'], data=return_data, child_accessor=child_accessor, **return_kwargs)
        else:
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