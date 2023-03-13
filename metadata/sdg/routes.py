import re
from flask import render_template, request
from natsort import natsorted
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from urllib.parse import quote, unquote, unquote_plus
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
def _expand():
    lang = request.args.get('amp;lang', 'en')
    print(f'For expansion, I have {lang}')
    rdf_type = request.args.get('amp;rdf_type')
    uri = unquote(request.args.get('uri'))
    this_id = request.args.get('amp;id')
    print(uri)

    if rdf_type == 'goal':
        goal_graph = build_graph(uri, endpoint)
        goal = {}
        goal['gid'] = this_id
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

        print(goal['targets'])

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
def about():
    lang = get_preferred_language(request)
    return render_template('sdg_about.html', lang=lang, site_lang=lang)

@sdg_app.route('/<id>')
def get_concept(id):
    lang = get_preferred_language(request)
    uri = "/".join([Config.base_uri,str(id)])
    return_data = get_goal(uri, lang)

    return render_template(return_data['template'], data=return_data, lang=lang, site_lang=lang, **return_kwargs)

def get_goal(uri, lang):
    graph = build_graph(uri, endpoint)
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
        print(em)
        ext_label = fetch_external_label(em, lang)
        
        print(f'External label: {ext_label}')
        if ext_label is None:
            continue
        return_data['skos:exactMatch'].append({
            'uri': em,
            'label': ext_label['label'],
            'source': ext_label['source']
        })
    print(return_data)
    return return_data

def get_target(uri, lang):
    graph = build_graph(uri, endpoint)
    return_data = {
        'uri': uri.replace(Config.base_uri, Config.local_base_uri),
        'skos:prefLabel': get_pref_label(uri, graph, lang),
        'rdf:type': [graph.qname(o) for s,p,o in graph.triples((None, RDF.type, None))],
        'skos:note': get_lexical_literal(uri, graph, SKOS.note, lang),
        'skos:inScheme': [o for s,p,o in graph.triples((None, SKOS.inScheme, None))],
        'sdgo:isTargetOf': [o for s,p,o in graph.triples((None, SDGO.isTargetOf, None))],
        'dct:subject': [],  # Empty so we can label it
        'sdgo:hasIndicator': [],   # Empty so we can label it
    }
    print(return_data)
    return render_template('sdg_target.html', data=return_data, lang=lang, site_lang=lang)

def get_indicator(uri, lang):
    graph = build_graph(uri, endpoint)
    return_data = {
        'uri': uri.replace(Config.base_uri, Config.local_base_uri),
        'skos:prefLabel': get_pref_label(uri, graph, lang),
        'rdf:type': [graph.qname(o) for s,p,o in graph.triples((None, RDF.type, None))],
        'skos:note': get_lexical_literal(uri, graph, SKOS.note, lang),
        'skos:inScheme': [o for s,p,o in graph.triples((None, SKOS.inScheme, None))],
        'sdgo:isIndicatorOf': [o for s,p,o in graph.triples((None, SDGO.isIndicatorOf, None))],
        'sdgo:tier': [o for s,p,o in graph.triples((None, SDGO.tier, None))],
        'dct:subject': [],  # Empty so we can label it
        'sdgo:hasSeries': [],   # Empty so we can label it
    }
    print(return_data)
    return render_template('sdg_indicator.html', data=return_data, lang=lang, site_lang=lang)

def get_series(uri, lang):
    graph = build_graph(uri, endpoint)
    return_data = {
        'uri': uri.replace(Config.base_uri, Config.local_base_uri),
        'skos:prefLabel': get_pref_label(uri, graph, lang),
        'rdf:type': [graph.qname(o) for s,p,o in graph.triples((None, RDF.type, None))],
        'skos:note': get_lexical_literal(uri, graph, SKOS.note, lang),
        'skos:inScheme': [o for s,p,o in graph.triples((None, SKOS.inScheme, None))],
        'sdgo:isSeriesOf': [o for s,p,o in graph.triples((None, SDGO.isSeriesOf, None))],
        'dct:subject': [],  # Empty so we can label it
    }
    print(return_data)
    return render_template('sdg_series.html', data=return_data, lang=lang, site_lang=lang)