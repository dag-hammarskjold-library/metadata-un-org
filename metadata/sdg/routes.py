import re
from flask import render_template, request, abort, Response
from flask_accept import accept
from natsort import natsorted
from rdflib import Graph, RDF, RDFS, OWL, Namespace, URIRef
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from urllib.parse import quote, unquote, unquote_plus
from os.path import join, dirname, realpath
from metadata.lib.gsparql import build_graph, get_pref_label, SDGO, get_lexical_literal, fetch_external_label
from metadata.sdg import sdg_app
from metadata.sdg.config import Config

return_kwargs = {
    'title': Config.INIT['title']
}

def get_match_class_by_regex(match_classes, pattern):
    return(next(filter(lambda m: re.compile(m['id_regex']).match(pattern),match_classes), None))

def get_match_class_by_name(match_classes, name):
    return(next(filter(lambda m: m['name'] == name ,match_classes), None))

def get_preferred_language(request):
    pref_lang = request.args.get('lang', request.accept_languages.best_match(Config.LANGUAGES.keys()))
    if pref_lang is None:
        pref_lang = 'en'
    return pref_lang

endpoint = Config.spqarql_endpoint + Config.repository_name

@sdg_app.route('/')
@accept('text/html')
def index():
    lang = get_preferred_language(request)
    this_c = get_match_class_by_name(Config.match_classes,'Root')
    root_concept = build_graph(this_c['scheme_uri'], endpoint)

    return_data = {
        'prefLabel': get_pref_label(this_c['scheme_uri'], root_concept, lang),
        'goals': []
    }

    goals = natsorted([o for s, p, o in root_concept.triples((None, SKOS.hasTopConcept, None))])
    for goal in goals:
        goal_uri = goal.replace(Config.base_uri, Config.local_base_uri)
        return_data['goals'].append({
            'id': goal_uri.split('/')[-1].zfill(2),
            'uri': goal_uri
        })

    return render_template('sdg_index.html', data=return_data, lang=lang, site_lang=lang, **return_kwargs)

@sdg_app.route('/_expand')
@accept('text/html')
def _expand():
    lang = request.args.get('amp;lang', 'en')
    #print(f'For expansion, I have {lang}')
    rdf_type = request.args.get('amp;rdf_type')
    uri = unquote(request.args.get('uri'))
    this_id = request.args.get('amp;id')
    #print(uri)

    if rdf_type == 'goal':
        goal_graph = build_graph(uri, endpoint)
        goal = {}
        goal['gid'] = this_id
        goal['uri'] = uri
        goal['note'] = get_lexical_literal(uri, goal_graph, SKOS.note, lang)
        goal['prefLabel'] = get_pref_label(uri, goal_graph, lang)
        goal['altLabels'] = get_lexical_literal(uri, goal_graph, SKOS.altLabel, lang)
        goal['targets'] = []
        
        targets = [o for s,p,o in goal_graph.triples((None, SDGO.hasTarget, None))]
        for target in targets:
            goal['targets'].append({
                'id': target.split('/')[-1],
                'uri': target
            })

        #print(goal['targets'])

        return render_template('sdg__goal.html', goal=goal, lang=lang)
    elif rdf_type == 'target':
        target_graph = build_graph(uri, endpoint)
        target = {
            'id': uri.split('/')[-1],
            'uri': uri.replace(Config.base_uri, Config.local_base_uri),
            'note': get_lexical_literal(uri, target_graph, SKOS.note, lang),
            'prefLabel': get_pref_label(uri, target_graph, lang),
            'indicators': []
        }
        indicators = [o for s,p,o in target_graph.triples((None, SDGO.hasIndicator, None))]
        for indicator in indicators:
            indicator_graph = build_graph(uri, endpoint)
            target['indicators'].append({
                'id': uri.split('/')[-1],
                'uri': uri.replace(Config.base_uri, Config.local_base_uri),
                'note': get_lexical_literal(uri, indicator_graph, SKOS.note, lang),
                'prefLabel': get_pref_label(uri, indicator_graph, lang)
            })

        return render_template('sdg__target.html', target=target, lang=lang)
    else:
        pass

@sdg_app.route('/about')
@accept('text/html')
def about():
    lang = get_preferred_language(request)
    return render_template('sdg_about.html', lang=lang, site_lang=lang)

@sdg_app.route('/<id>')
@accept('text/html')
def get_concept(id):
    lang = get_preferred_language(request)
    uri = "/".join([Config.base_uri,str(id)])
    if re.match("^\d{1,2}$",id):
        return_data = get_goal(uri, lang)
    elif re.match("^\d{1,2}.[a-zA-Z0-9]{1,2}$", id):
        return_data = get_target(uri, lang)
    elif re.match("^C[a-zA-Z-0-9]{6,6}$", id):
        return_data = get_indicator(uri, lang)
    else:
        # Series patterns aren't as easily predictable, so it will be important to 
        # screen out bad attempts quickly and return a 404
        return_data = get_series(uri, lang)

    return render_template(return_data['template'], data=return_data, lang=lang, site_lang=lang, **return_kwargs)

def get_goal(uri, lang):
    graph = build_graph(uri, endpoint)
    if graph is None:
        abort(404)
    return_data = {
        'template': 'sdg_goal.html',
        'uri': uri.replace(Config.base_uri, Config.local_base_uri),
        'skos:prefLabel': get_pref_label(uri, graph, lang),
        'rdf:type': [{'uri': o, 'label': graph.qname(o)} for s,p,o in graph.triples((None, RDF.type, None)) if 'sdgo' in graph.qname(o)][0],
        'skos:note': get_lexical_literal(uri, graph, SKOS.note, lang),
        'skos:inScheme': [o for s,p,o in graph.triples((None, SKOS.inScheme, None))],
        'dct:subject': [],  # Empty so we can label it
        'sdgo:hasTarget': [],   # Empty so we can label it
        'skos:exactMatch': []
    }
    subjects = natsorted([o for s,p,o in graph.triples((None, DCTERMS.subject, None))])
    for subject in subjects:
        ext_label = fetch_external_label(subject, lang)
        return_data['dct:subject'].append({
            'uri': subject,
            'label': ext_label['label'],
            'source': ext_label['source']
        })
    targets = natsorted([o for s,p,o in graph.triples((None, SDGO.hasTarget, None))])
    for target in targets:
        target_graph = build_graph(target, endpoint)
        return_data['sdgo:hasTarget'].append({
            'uri': target,
            'note': get_lexical_literal(target, target_graph, SKOS.note, lang),
            'label': get_pref_label(target, target_graph, lang)
        })
    exact_matches = natsorted([o for s,p,o in graph.triples((None, SKOS.exactMatch, None))])
    for em in exact_matches:
        #print(em)
        ext_label = fetch_external_label(em, lang)
        
        #print(f'External label: {ext_label}')
        if ext_label is None:
            continue
        return_data['skos:exactMatch'].append({
            'uri': em,
            'label': ext_label['label'],
            'source': ext_label['source']
        })
    return return_data

def get_target(uri, lang):
    graph = build_graph(uri, endpoint)
    if graph is None:
        abort(404)
    return_data = {
        'template': 'sdg_target.html',
        'uri': uri.replace(Config.base_uri, Config.local_base_uri),
        'skos:prefLabel': get_pref_label(uri, graph, lang),
        'rdf:type': [{'uri': o, 'label': graph.qname(o)} for s,p,o in graph.triples((None, RDF.type, None)) if 'sdgo' in graph.qname(o)][0],
        'skos:note': get_lexical_literal(uri, graph, SKOS.note, lang),
        'skos:inScheme': [o for s,p,o in graph.triples((None, SKOS.inScheme, None))],
        'sdgo:isTargetOf': [],
        'dct:subject': [],  # Empty so we can label it
        'sdgo:hasIndicator': [],   # Empty so we can label it
    }
    goals = natsorted([o for s,p,o in graph.triples((None, SDGO.isTargetOf, None))])
    for goal in goals:
        goal_graph = build_graph(goal, endpoint)
        return_data['sdgo:isTargetOf'].append({
            'uri': goal,
            'note': get_lexical_literal(goal, goal_graph, SKOS.note, lang),
            'label': get_pref_label(goal, goal_graph, lang)
        })
    indicators = natsorted([o for s,p,o in graph.triples((None, SDGO.hasIndicator, None))])
    for indicator in indicators:
        indicator_graph = build_graph(indicator, endpoint)
        return_data['sdgo:hasIndicator'].append({
            'uri': indicator,
            'note': get_lexical_literal(indicator, indicator_graph, SKOS.note, lang),
            'label': get_pref_label(indicator, indicator_graph, lang)
        })
    subjects = natsorted([o for s,p,o in graph.triples((None, DCTERMS.subject, None))])
    for subject in subjects:
        ext_label = fetch_external_label(subject, lang)
        return_data['dct:subject'].append({
            'uri': subject,
            'label': ext_label['label'],
            'source': ext_label['source']
        })
    return return_data

def get_indicator(uri, lang):
    graph = build_graph(uri, endpoint)
    if graph is None:
        abort(404)
    return_data = {
        'template': 'sdg_indicator.html',
        'uri': uri.replace(Config.base_uri, Config.local_base_uri),
        'skos:prefLabel': get_pref_label(uri, graph, lang),
        'rdf:type': [{'uri': o, 'label': graph.qname(o)} for s,p,o in graph.triples((None, RDF.type, None)) if 'sdgo' in graph.qname(o)][0],
        'skos:note': get_lexical_literal(uri, graph, SKOS.note, lang),
        'skos:inScheme': [o for s,p,o in graph.triples((None, SKOS.inScheme, None))],
        'sdgo:tier': [o for s,p,o in graph.triples((None, SDGO.tier, None))],
        'sdgo:isIndicatorOf': [],
        'dct:subject': [],  # Empty so we can label it
        'sdgo:hasSeries': [],   # Empty so we can label it
    }
    targets = natsorted([o for s,p,o in graph.triples((None, SDGO.isIndicatorOf, None))])
    for target in targets:
        target_graph = build_graph(target, endpoint)
        return_data['sdgo:isIndicatorOf'].append({
            'uri': target,
            'note': get_lexical_literal(target, target_graph, SKOS.note, lang),
            'label': get_pref_label(target, target_graph, lang)
        })
    series = natsorted([o for s,p,o in graph.triples((None, SDGO.hasSeries, None))])
    for s in series:
        series_graph = build_graph(s, endpoint)
        return_data['sdgo:hasSeries'].append({
            'uri': s,
            #'note': get_lexical_literal(s, series_graph, SKOS.note, lang),
            'label': get_pref_label(s, series_graph, lang)
        })
    subjects = natsorted([o for s,p,o in graph.triples((None, DCTERMS.subject, None))])
    for subject in subjects:
        ext_label = fetch_external_label(subject, lang)
        return_data['dct:subject'].append({
            'uri': subject,
            'label': ext_label['label'],
            'source': ext_label['source']
        })
    return return_data

def get_series(uri, lang):
    graph = build_graph(uri, endpoint)
    if graph is None:
        abort(404)
    return_data = {
        'template': 'sdg_series.html',
        'uri': uri.replace(Config.base_uri, Config.local_base_uri),
        'skos:prefLabel': get_pref_label(uri, graph, lang),
        'rdf:type': [{'uri': o, 'label': graph.qname(o)} for s,p,o in graph.triples((None, RDF.type, None)) if 'sdgo' in graph.qname(o)][0],
        #'skos:note': get_lexical_literal(uri, graph, SKOS.note, lang),
        'skos:inScheme': [o for s,p,o in graph.triples((None, SKOS.inScheme, None))],
        'sdgo:tier': [o for s,p,o in graph.triples((None, SDGO.tier, None))],
        'sdgo:isSeriesOf': [],
        'dct:subject': [],  # Empty so we can label it
    }
    indicators = natsorted([o for s,p,o in graph.triples((None, SDGO.isSeriesOf, None))])
    for target in indicators:
        target_graph = build_graph(target, endpoint)
        return_data['sdgo:isSeriesOf'].append({
            'uri': target,
            'note': get_lexical_literal(target, target_graph, SKOS.note, lang),
            'label': get_pref_label(target, target_graph, lang)
        })
    series = natsorted([o for s,p,o in graph.triples((None, SDGO.hasSeries, None))])
    for s in series:
        series_graph = build_graph(s, endpoint)
        return_data['sdgo:hasSeries'].append({
            'uri': s,
            'note': get_lexical_literal(s, series_graph, SKOS.note, lang),
            'label': get_pref_label(s, series_graph, lang)
        })
    subjects = natsorted([o for s,p,o in graph.triples((None, DCTERMS.subject, None))])
    for subject in subjects:
        ext_label = fetch_external_label(subject, lang)
        return_data['dct:subject'].append({
            'uri': subject,
            'label': ext_label['label'],
            'source': ext_label['source']
        })
    return return_data

@sdg_app.route('/ontology')
@accept('text/html')
def ontology():
    lang = get_preferred_language(request)

    ontology_path = join(dirname(realpath(__file__)), 'static/sdgs-ontology.ttl')

    g = Graph()
    g.parse(ontology_path,format='ttl')

    data = {
        'IRI': 'http://metadata.un.org/sdg/ontology',
        'classes': [],
        'objectProperties': [],
        'dataTypeProperties': [],
        'instances':[],
        'namespaces': [],
        'default_namespace': ''
    }
    namepsaces = []
    for q,n in g.namespaces():
        if len(q) == 0:
            data['default_namespace'] = ('default (:)',n)
        else:
            namepsaces.append((q,n))
    data['namespaces'] = sorted(namepsaces)

    rdf_types = [
        ('classes','http://www.w3.org/2002/07/owl#Class'),
        ('objectProperties','http://www.w3.org/2002/07/owl#ObjectProperty'),
        ('dataTypeProperties','http://www.w3.org/2002/07/owl#DatatypeProperty'),
        ('instances','http://metadata.un.org/sdg/ontology#Tier')
    ]
    for n,t in rdf_types:
        classes = []
        for s in g.subjects(predicate=URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), object=URIRef(t)):
            this_c = {
                'IRI': s,
                'name': g.qname(s),
                'triples': []
            }
            triples = []
            for p,o in g.predicate_objects(subject=s):
                try:
                    if "metadata.un.org" in o or "unstats.un.org" in o:
                        this_t = (g.qname(s),g.qname(p),o,'isUri')
                        triples.append(this_t)
                    else:
                        this_t = (g.qname(s),g.qname(p),g.qname(o),'isqName')
                        triples.append(this_t)
                except Exception:
                    this_t = (g.qname(s),g.qname(p),o,'isText')
                    triples.append(this_t)
            this_c['triples'] = sorted(triples, key=lambda x: x[1])
            classes.append(this_c)
        data[n] = sorted(classes, key=lambda x: x['name'])

    return render_template('_sdg_ontology.html', data=data, lang=lang, site_lang=lang)

@ontology.support('text/turtle', 'application/ld+json', 'application/rdf+xml')
def ontology_formatted():
    ontology_path = join(dirname(realpath(__file__)), 'static/sdgs-ontology.ttl')

    g = Graph()
    g.parse(ontology_path,format='ttl')

    this_mimetype = str(request.accept_mimetypes)
    if this_mimetype == 'application/ld+json':
        return Response(g.serialize(format='json-ld'), mimetype='application/ld+json; charset=utf-8')
    elif this_mimetype == 'application/rdf+xml':
        return Response(g.serialize(format='xml'), mimetype='application/rdf+xml')
    else:
        return Response(g.serialize(format='ttl'), mimetype='text/turtle')

@sdg_app.route('/void.ttl')
#@void.support('text/turtle', 'application/ld+json', 'application/rdf+xml')
def void():
    void_path = join(dirname(realpath(__file__)), 'static/void.ttl')

    g = Graph()
    g.parse(void_path,format='ttl')

    return Response(g.serialize(format='ttl'), mimetype='text/turtle')

@index.support('text/turtle', 'application/ld+json', 'application/rdf+xml')
def get_serialize_root():
    graph = build_graph(Config.base_uri, endpoint)
    if graph is None:
        abort(404)
    
    this_mimetype = str(request.accept_mimetypes)
    if this_mimetype == 'application/ld+json':
        return Response(graph.serialize(format='json-ld'), mimetype='application/json; charset=utf-8')
    elif this_mimetype == 'application/rdf+xml':
        return Response(graph.serialize(format='xml'), mimetype='application/rdf+xml')
    else:
        # Fallback to turtle
        return Response(graph.serialize(format='ttl'), mimetype='text/turtle')

@get_concept.support('text/turtle', 'application/ld+json', 'application/rdf+xml')
def get_serialized_rdf(id):
    uri = "/".join([Config.base_uri,str(id)])
    graph = build_graph(uri, endpoint)
    if graph is None:
        abort(404)
    
    this_mimetype = str(request.accept_mimetypes)
    if this_mimetype == 'application/ld+json':
        return Response(graph.serialize(format='json-ld'), mimetype='application/json; charset=utf-8')
    elif this_mimetype == 'application/rdf+xml':
        return Response(graph.serialize(format='xml'), mimetype='application/rdf+xml')
    else:
        # Fallback to turtle
        return Response(graph.serialize(format='ttl'), mimetype='text/turtle')