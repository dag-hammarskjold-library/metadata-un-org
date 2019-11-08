from flask import render_template, redirect, url_for, request, jsonify, abort, json, Response
from flask_babel import Babel, gettext
from flask_accept import accept
from elasticsearch import Elasticsearch
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
from werkzeug.contrib.cache import SimpleCache
from mongoengine import connect
from metadata import cache
from metadata.lib.poolparty import PoolParty, Thesaurus
from metadata.lib.ppmdb import Concept
from metadata.lib.rdf import graph_concept
from metadata.sdg import sdg_app
from metadata.sdg.config import CONFIG
from metadata.sdg.utils import get_or_update, replace_concept
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es
from urllib.parse import quote, unquote, unquote_plus
import re, requests, ssl, urllib



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

#cache = SimpleCache()

ssl_context = ssl.SSLContext()

connect(host=CONFIG.connect_string, db=CONFIG.db_name, ssl_cert_reqs=ssl.CERT_NONE)

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
        goal_id = goal_uri['uri'].split("/")[-1].zfill(2)
        this_goal = {
            'id': goal_id,
            'uri': goal_uri
        }
        goals.append(this_goal)

    return_data['goals'] = sorted(goals, key=lambda x: x['id'])

    return render_template(this_c['template'], data=return_data, **return_kwargs)


@sdg_app.route('/<id>', methods=['GET'])
@accept('text/html')
def get_concept(id):
    uri = INIT['uri_base'] + id
    if re.match(r'\d{1,2}.\d{1,2}.\d{1,2}',id):
        uri = Concept.objects(__raw__={'rdf_properties.object.label': id})[0].uri
        id = uri.split("/")[-1]

    get_preferred_language(request, return_kwargs)
    return_data = {}
    
    pid = id.split(".")[0].zfill(2)

    this_c = get_match_class_by_regex(CONFIG.match_classes,id)
    if this_c is not None:
        concept = get_or_update(uri)
        return_data = {
            'URI': concept.uri,
            'skos:prefLabel': concept.pref_label(return_kwargs['lang']).label
        }
        if len(concept.alt_labels) > 0:
            return_data['skos:altLabel'] = [x.label for x in concept.alt_labels]
        

        notes = concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note')
        if notes is not None:
            return_data['skos:note'] = filter(lambda x: x['language'] == return_kwargs['lang'], notes.object)

        in_schemes = concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#inScheme').object
        return_data['skos:inScheme'] = in_schemes

        broaders = concept.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#broader')
        if broaders:
            this_broaders = []
            for b in broaders.object:
                c = get_or_update(b['uri'])
                b['pref_label'] = c.pref_label(return_kwargs['lang'])
                notes = c.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
                #print(pid, notes)
                b['note'] = next(filter(lambda x: x['language'] == return_kwargs['lang'],notes),None)

                this_broaders.append(b)
            return_data['skos:broader'] = this_broaders

        tiers = concept.get_property_by_predicate('http://metadata.un.org/sdg/ontology#tier')
        if tiers:
            return_data['sdgo:tier'] = tiers.object

        if this_c['children'] is not None:
            child_accessor = this_c['children']['name']
            this_children = []
            print(this_c['children'])
            child_uris = concept.get_property_by_predicate(this_c['children']['uri'])
            if child_uris is not None:
                for child_uri in child_uris.object:
                    child = get_or_update(child_uri['uri'])
                    if this_c['children']['sort_children_by'] is not None:
                        sort_key, attr, sort_length = this_c['children']['sort_children_by']
                    child.pid = id.split(".")[0].zfill(2)
                    notes = child.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note')
                    if notes is not None:
                        child.note = next(filter(lambda x: x['language'] == return_kwargs['lang'] and x['label'].split(".")[0].split(" ")[1].zfill(2) == child.pid,notes.object),None)
                    else:
                        child.note = None
                    notations = child.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#notation').object
                    child.notation = next(filter(lambda x: x['label'].split(".")[0] == child.pid, notations),None)

                    this_children.append(child)
                print(this_children)
                if this_c['children']['sort_children_by'] is not None:
                    return_data[this_c['children']['name']] = sorted(this_children, key=lambda x: x.notation['label'])
                else:
                    return_data[this_c['children']['name']] = this_children
            else:
                return_data[this_c['children']['name']] = None
        else:
            child_accessor = None
            
        #except:
        #    abort(404)

        return render_template(this_c['template'], data=return_data, child_accessor=child_accessor, **return_kwargs)
    else:
        abort(404)

@sdg_app.route('/<id>', methods=['POST'])
def put_concept(id):
    uri = INIT['uri_base'] + id
    if re.match(r'\d{1,2}.\d{1,2}.\d{1,2}',id):
        uri = Concept.objects(__raw__={'rdf_properties.object.label': id})[0].uri
        id = uri.split("/")[-1]

    cache_key = request.form.get('cache_key',None)
    if cache_key == GLOBAL_CONFIG.CACHE_KEY:
        res = replace_concept(uri)
        print(res)
        if res:
            return Response(json.dumps({"success":"true"}), status=200, mimetype='application/json')
        else:
            return Response(json.dumps({"success":"false"}), status=500, mimetype='application/json')
    else:
        abort(403)

@get_concept.support('text/turtle')
def get_concept_turtle(id):
    uri = INIT['uri_base'] + id
    if re.match(r'\d{1,2}.\d{1,2}.\d{1,2}',id):
        uri = Concept.objects(__raw__={'rdf_properties.object.label': id})[0].uri
        id = uri.split("/")[-1]
        
    concept = get_or_update(uri)
    concept_graph = graph_concept(concept)
    return Response(concept_graph.serialize(format='ttl'), mimetype='text/turtle')

@get_concept.support('application/json')
def get_concept_json(id):
    uri = INIT['uri_base'] + id
    if re.match(r'\d{1,2}.\d{1,2}.\d{1,2}',id):
        uri = Concept.objects(__raw__={'rdf_properties.object.label': id})[0].uri
        id = uri.split("/")[-1]

    concept = get_or_update(uri)
    concept_graph, context = graph_concept(concept)
    
    return Response(concept_graph.serialize(format='json-ld', context=context), mimetype='application/json; charset=utf-8')

@get_concept.support('application/rdf+xml')
def get_concept_xml(id):
    uri = INIT['uri_base'] + id
    if re.match(r'\d{1,2}.\d{1,2}.\d{1,2}',id):
        uri = Concept.objects(__raw__={'rdf_properties.object.label': id})[0].uri
        id = uri.split("/")[-1]
        
    concept = get_or_update(uri)
    concept_graph = graph_concept(concept)
    return Response(concept_graph.serialize(format='xml'), mimetype='application/rdf+xml')

@sdg_app.route('/_expand')
def _expand():
    #get_preferred_language(request, return_kwargs)
    lang = request.args.get('amp;lang','en')
    return_kwargs['lang'] = lang
    print(return_kwargs['lang'])
    rdf_type = request.args.get('amp;rdf_type')
    uri = unquote(request.args.get('uri'))
    this_id = request.args.get('amp;id')
    #print(this_id, rdf_type,uri, return_kwargs['lang'])
    if rdf_type == 'goal':
        goal = get_or_update(uri)
        goal.gid = this_id
        notes = goal.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
        goal.note = next(filter(lambda x: x['language'] == return_kwargs['lang'],notes),None)
        notations = goal.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#notation').object
        goal.notation = next(filter(lambda x: len(x['label']) == 2,notations),None)
        targets = []
        for target_uri in goal.get_property_by_predicate('http://metadata.un.org/sdg/ontology#hasTarget').object:
            target_id = ".".join(list(map(lambda x: x.zfill(2), target_uri['uri'].split('/')[-1].split("."))))
            this_target = {
                'id': target_id,
                'uri': target_uri
            }
            targets.append(this_target)
        goal.targets = sorted(targets, key=lambda x: x['id'])

        return render_template('sdg__goal.html', goal=goal, **return_kwargs)
    elif rdf_type == 'target':
        target = get_or_update(uri)
        target.gid = this_id
        target.goal_id = this_id.split(".")[0]
        #print("Goal ID: ",target.goal_id)
        notes = target.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
        target.note = next(filter(lambda x: x['language'] == return_kwargs['lang'],notes),None)
        notations = target.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#notation').object
        target.notation = next(filter(lambda x: len(x['label']) == 5,notations),None)

        indicators = []
        for indicator_uri in target.get_property_by_predicate('http://metadata.un.org/sdg/ontology#hasIndicator').object:
            indicator = get_or_update(indicator_uri['uri'])
            notes = indicator.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#note').object
            indicator.note = next(filter(lambda x: x['language'] == return_kwargs['lang'] and x['label'].split(".")[0].split(" ")[1].zfill(2) == target.goal_id,notes),None)
            #print("Indicator Note: ",indicator.note)
            notations = indicator.get_property_by_predicate('http://www.w3.org/2004/02/skos/core#notation').object
            indicator.notation = next(filter(lambda x: x['label'].split(".")[0] == target.goal_id, notations),None)
            indicators.append(indicator)
        
        target.indicators = sorted(indicators, key=lambda x: x.notation['label'])

        return render_template('sdg__target.html', target=target, **return_kwargs)
    else:
        pass

@sdg_app.route('/ontology')
def ontology():
    get_preferred_language(request, return_kwargs)
    
    return render_template('sdg_ontology.html', **return_kwargs)

@sdg_app.route('/about')
def about():
    return render_template('sdg_about.html', **return_kwargs)