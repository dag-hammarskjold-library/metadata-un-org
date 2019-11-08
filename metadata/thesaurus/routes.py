from flask import render_template, redirect, url_for, request, jsonify, abort, json, Response
from flask_babel import Babel, gettext
from flask_accept import accept
from elasticsearch import Elasticsearch
from rdflib import Graph, term, URIRef, Literal, Namespace, RDF
from rdflib.namespace import SKOS
from metadata import cache
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es, Pagination
from bson.json_util import dumps
from metadata.thesaurus.utils import get_or_update, replace_concept, reindex_concept
from urllib.parse import quote
from mongoengine import connect
from metadata.lib.rdf import graph_concept
from metadata.lib.ppmdb import Concept, Label, Relationship, reload_concept
from metadata.lib.poolparty import PoolParty, Thesaurus, History
import re, requests, ssl


INIT = CONFIG.INIT
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS
valid_formats = ['json','ttl', 'xml']

connect(host=CONFIG.connect_string, db='undhl-issu', ssl_cert_reqs=ssl.CERT_NONE)

pool_party = PoolParty(CONFIG.endpoint, CONFIG.project_id, CONFIG.username, CONFIG.password)
thesaurus = Thesaurus(pool_party)
history = History(pool_party)

ES_CON = Elasticsearch(CONFIG.ELASTICSEARCH_URI)

# Common set of kwargs to return in all cases. 
return_kwargs = {
    **CONFIG.KWARGS,
    **GLOBAL_KWARGS
}
return_kwargs['valid_formats'] = valid_formats

def get_match_class_by_regex(match_classes, pattern):
    return(next(filter(lambda m: re.compile(m['id_regex']).match(pattern),match_classes), None))

def get_match_class_by_name(match_classes, name):
    return(next(filter(lambda m: m['name'] == name ,match_classes), None))


@thesaurus_app.route('/')
@accept('text/html')
def index():
    '''
    This should return a landing page for the thesaurus application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    get_preferred_language(request, return_kwargs)
    root_uri = INIT['uri_base'] + '00'

    return_data = {}

    concept = get_or_update(uri=root_uri, languages=return_kwargs['available_languages'])
    return_data['URI'] = concept.uri
    return_data['pref_label'] = concept.pref_label(return_kwargs['lang'])

    this_concept_schemes = []
    for cs in concept.get_property_by_predicate('http://purl.org/dc/terms/hasPart').object:
        this_data = {}
        this_cs = get_or_update(uri=cs['uri'], languages=return_kwargs['available_languages'])
        this_data['uri'] = this_cs.uri
        this_data['pref_label'] = this_cs.pref_label(return_kwargs['lang'])
        this_data['identifier'] = this_cs.get_property_by_predicate('http://purl.org/dc/elements/1.1/identifier').object[0]['label']
        this_concept_schemes.append(this_data)
    return_data['Concept Schemes'] = sorted(this_concept_schemes, key=lambda x: x['identifier'])
    

    this_language_equivalents = []
    for lang in CONFIG.LANGUAGES:
        this_language_equivalents.append(next(filter(lambda x: x.language == lang, concept.pref_labels),None))
    return_data['Language Equivalents'] = this_language_equivalents

    version = concept.get_property_by_predicate('http://purl.org/dc/terms/hasVersion')
    return_data['Version'] = version.object[0]['label']
    

    return render_template('thesaurus_index.html', data=return_data, **return_kwargs)

@thesaurus_app.route('/T<id>')
def get_by_tcode(id):
    this_id = "T" + id
    id_regex = r'^T\d+'
    p = re.compile(id_regex)
    if not p.match(this_id):
        abort(500)
    dsl_q = '''{ "query": { "match": { "tcode": "%s" } } }''' % this_id
				
    try:
        this_uri = ES_CON.search(index=CONFIG.INDEX_NAME, body=dsl_q)['hits']['hits'][0]['_source']['uri']
    except IndexError:
        abort(404)
    return jsonify({"id": this_id, "uri": this_uri})


@thesaurus_app.route('/<id>')
@accept('text/html')
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
        concept = get_or_update(uri=this_uri, languages=return_kwargs['available_languages'])
        
        try:
            return_data['URI'] = concept.uri
        except AttributeError:
            return render_template('404.html', **return_kwargs), 404

        return_data['Preferred Term'] = concept.pref_label(return_kwargs['lang'])
        
        this_language_equivalents = []
        for lang in CONFIG.LANGUAGES:
            this_language_equivalents.append(next(filter(lambda x: x.language == lang, concept.pref_labels),None))
        return_data['Language Equivalents'] = this_language_equivalents

        this_scope_notes = filter(lambda x: x['language'] == return_kwargs['lang'], concept.scope_notes)
        scope_notes = []
        for sn in this_scope_notes:
            scope_notes.append(sn)
        
        if len(scope_notes) > 0:
            return_data['scopeNotes'] = scope_notes

        if this_c['children'] is not None:
            #print(this_c)
            for child_def in this_c['children']:
                this_child_data = []
                this_children = []
                try:
                    this_children = concept.get_property_by_predicate(child_def['uri']).object
                except AttributeError:
                    next
                for child in this_children:
                    #print(child)
                    this_data = {}
                    this_child = get_or_update(uri=child['uri'], languages=return_kwargs['available_languages'])
                    this_data['uri'] = this_child.uri
                    this_data['pref_label'] = this_child.pref_label(return_kwargs['lang'])
                    for name,uri in child_def['attributes']:
                        #print(name,uri)
                        this_data[name] = this_child.get_property_by_predicate(uri).object[0]['label']
                    this_child_data.append(this_data)
                
                if child_def['sort'] is not None:
                    return_data[child_def['name']] = sorted(this_child_data, key=lambda x: x[child_def['sort']])
                else:
                    return_data[child_def['name']] = sorted(this_child_data, key=lambda x: x['pref_label'].label)
        
        
        this_breadcrumbs = list(filter(lambda x: x['language'] == return_kwargs['lang'],concept.breadcrumbs))
        if len(this_breadcrumbs) > 0:
            return_data['breadcrumbs'] = sorted(this_breadcrumbs, key=lambda x: x['breadcrumb']['domain']['identifier'])

        return render_template(this_c['template'], data=return_data, **return_kwargs)
    else:
        return render_template('404.html', **return_kwargs), 404

@index.support('text/turtle', 'application/json', 'application/rdf+xml')
def get_root_export():
    return redirect(url_for('thesaurus.get_by_id', id='00'))
 
@get_by_id.support('application/json')
def get_json(id):
    return redirect(url_for('thesaurus.get_concept_and_format', id=id, format='json'))

@get_by_id.support('application/rdf+xml')
def get_xml(id):
    return redirect(url_for('thesaurus.get_concept_and_format', id=id, format='xml'))

@get_by_id.support('text/turtle')
def get_ttl(id):
    return redirect(url_for('thesaurus.get_concept_and_format', id=id, format='ttl'))

@thesaurus_app.route('/<id>.<format>')
def get_concept_and_format(id,format):
    uri = INIT['uri_base'] + id
    concept = get_or_update(uri)
    concept_graph, context = graph_concept(concept)

    if format in valid_formats:
        if format == 'json':
            mimetype = 'application/json; charset=utf-8'
            return Response(concept_graph.serialize(format='json-ld',context=context), mimetype=mimetype)
        elif format == 'xml':
            mimetype = 'application/rdf+xml'
            return Response(concept_graph.serialize(format='xml'), mimetype=mimetype)
        else:
            return Response(concept_graph.serialize(format='ttl'), mimetype='text/turtle')
    else:
        return Response(concept_graph.serialize(format='ttl'), mimetype='text/turtle')
    
'''
@get_concept.support('text/turtle')
def get_concept_turtle(id):
    uri = INIT['uri_base'] + id
    if re.match(r'\d{1,2}.\d{1,2}.\d{1,2}',id):
        uri = Concept.objects(__raw__={'rdf_properties.object.label': id})[0].uri
        id = uri.split("/")[-1]
        
    concept = get_or_update(uri)
    concept_graph, context = graph_concept(concept)
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
    concept_graph, context = graph_concept(concept)
    return Response(concept_graph.serialize(format='xml'), mimetype='application/rdf+xml')
'''
@thesaurus_app.route('/categories')
def categories():
    get_preferred_language(request, return_kwargs)

    domains = Concept.objects(__raw__={
        'rdf_properties.predicate': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 
        'rdf_properties.object.uri': 'http://eurovoc.europa.eu/schema#Domain',
        'uri': re.compile('http\:\/\/metadata\.un\.org\/thesaurus*') 
    })

    for domain in domains:
        domain.identifier = domain.get_property_values_by_predicate('http://purl.org/dc/elements/1.1/identifier')[0]['label']
        microthesauri = domain.get_property_values_by_predicate('http://www.w3.org/2004/02/skos/core#hasTopConcept')
        domain.microthesauri = []

        for mt in microthesauri:
            microthesaurus = get_or_update(uri=mt['uri'], languages=return_kwargs['available_languages'])
            microthesaurus.identifier = microthesaurus.get_property_values_by_predicate('http://purl.org/dc/elements/1.1/identifier')[0]['label']
            domain.microthesauri.append(microthesaurus)

    return render_template('thesaurus_categories.html', data=domains, **return_kwargs)

@thesaurus_app.route('/alphabetical')
def alphabetical():
    get_preferred_language(request, return_kwargs)

    if return_kwargs['lang'] == 'zh':
        return render_template('thesaurus_alphabetical.html', data=url_for('static',filename='zh_sorted.json'),  **return_kwargs, subtitle=gettext('Browse Alphabetically'))

    concepts = Concept.objects(__raw__=
        {
            'rdf_properties.predicate': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 
            'rdf_properties.object.uri': 'http://www.w3.org/2004/02/skos/core#Concept',
            'uri': re.compile('http\:\/\/metadata\.un\.org\/thesaurus*'),
            'pref_labels.language': return_kwargs['lang']
        }).fields(uri=1,pref_labels={'$elemMatch': {'language': return_kwargs['lang']}})

    return_concepts = []
    for c in concepts:
        this_concept = {
            'uri': c['uri'],
            'pref_label': c['pref_labels'][0]['label']
        }
        return_concepts.append(this_concept)
    

    return render_template('thesaurus_alphabetical.html', data=sorted(return_concepts, key=lambda x: x['pref_label']), **return_kwargs, subtitle=gettext('Browse Alphabetically'))

@thesaurus_app.route('/new')
def term_updates():
    get_preferred_language(request, return_kwargs)
    '''
    api_path = '%shistory/%s?fromTime=%s&lang=%s' % (
        API['source'], INIT['thesaurus_pattern'].replace('thesaurus/',''), '2019-01-01T00:00:00', return_kwargs['lang']
    )
    '''
    return_data = history.get_events(fromTime='2019-01-01T00:00:00')
    #print(return_data)
    return render_template('thesaurus_new.html', data=return_data, **return_kwargs, subtitle=gettext('Updates'))

@thesaurus_app.route('/about')
def about():
    get_preferred_language(request, return_kwargs)
    
    return render_template('thesaurus_about.html', **return_kwargs, subtitle=gettext('About'))

@thesaurus_app.route('/search')
def search():
    import unicodedata
    index_name = CONFIG.INDEX_NAME
    query = request.args.get('q', None)
    if not query:
        referrer = request.referrer
        return redirect(referrer)
    preferred_language = request.args.get('lang', 'en')
    if not preferred_language:
        abort(500)
    page = request.args.get('page', '1')

    def remove_control_characters(s):
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    query = remove_control_characters(query)

    #print(ES_CON)

    match = query_es(ES_CON, index_name, query, preferred_language, 8000)
    count = match['hits']['total']
    #print(count)
    response = []
    # Strangely, we can't expect the fields we specify in our query to actually exist.
    for m in match['hits']['hits']:
        try:
            this_r = {
                'score': m['_score'],
                'pref_label': m['_source']['labels_%s' % preferred_language][0],
                'uri': m['_source']['uri'],
                'uf_highlights': []
            }
            try:
                this_h = m['highlight']['alt_labels_%s' % preferred_language]
                this_r['uf_highlights'] = this_h
            except KeyError:
                pass
            response.append(this_r)
        except KeyError:
            pass

    #resp = response[(int(page) - 1) * int(KWARGS['rpp']): (int(page) - 1) * int(KWARGS['rpp']) + int(KWARGS['rpp']) ]
    #pagination = Pagination(page, KWARGS['rpp'], len(response))
    #print('Search response:',response)

    #print(pagination.page, page)

    return render_template('thesaurus_search.html', results=response, query=query, count=count, lang=preferred_language, subtitle=gettext('Search'))

@thesaurus_app.route('/autocomplete', methods=['GET'])
def autocomplete():
    index_name = CONFIG.INDEX_NAME
    q = request.args.get('q', None)
    preferred_language = request.args.get('lang', 'en')
    if not q:
        abort(500)
    if not preferred_language:
        abort(500)

    match = query_es(ES_CON, index_name, q, preferred_language, 20)
    results = []
    for res in match['hits']['hits']:
        if not res['_source'].get("labels_%s" % preferred_language):
            continue
        uri = res["_source"]["uri"]
        #print(uri)
        pref_label = res["_source"]["labels_%s" % preferred_language][0]
        
        #print(pref_label)
        results.append({
            'uri': uri,
            'pref_label': pref_label
        })

    return jsonify(results)

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
            concept = reload_concept(uri, thesaurus, return_kwargs['available_languages'])
        except:
            return jsonify({'Status': 'Error: Either the operation timed out, or the concept was not found.'})
        
        reindex_concept(concept)
        return jsonify({'Status':'Success'})
    else:
        return render_template('404.html', **return_kwargs), 404
