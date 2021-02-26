import requests
import json
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode

def build_graph(uri, endpoint='http://localhost:7200/repositories/UNBIST_core'):
    # Takes a URI and requests everything we can learn about it from the given endpoint
    # Example request to build: http://metadata.un.org:7200/repositories/UNBIST_core?query=PREFIX%20%3A%20%3Chttp%3A%2F%2Fmetadata.un.org%2Fthesaurus%2F%3E%0ASELECT%20%3Fp%20%3Fo%20%7B%0A%20%20%20%20%3A010100%20%3Fp%20%3Fo%0A%7D%0A

    g = Graph()
    EU = Namespace('http://eurovoc.europa.eu/schema#')
    DC = Namespace('http://purl.org/dc/elements/1.1/')
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    UNBIST = Namespace('http://metadata.un.org/thesaurus/')
    SDG = Namespace('http://metadata.un.org/sdg/')
    SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

    g.bind('skos', SKOS)
    g.bind('eu', EU)
    g.bind('dc', DC)
    g.bind('dcterms', DCTERMS)
    g.bind('unbist', UNBIST)
    g.bind('sdg', SDG)
    g.bind('sdgo', SDGO)

    jsonld_context = {
        'skos': SKOS,
        'eu': EU,
        'dc': DC,
        'dcterms': DCTERMS,
        #'unbist': UNBIST,
        #'sdg': SDG,
        'sdgo': SDGO
    }

    params = {
        'query': f'SELECT ?p ?o {{ <{uri}> ?p ?o }}'
    }
    headers = {
        'Accept': 'application/json'
    }
    print(params)
    response = requests.get(endpoint, headers=headers, params=params)
    json_data = json.loads(response.text)
    for res in json_data['results']['bindings']:
        s = URIRef(uri)
        p = URIRef(res['p']['value'])
        # default for object is URI, but we'll override if it's a literal
        o = None
        if res['o']['type'] == 'uri':
            o = URIRef(res['o']['value'])
        elif res['o']['type'] == 'literal':
            if 'xml:lang' in res['o']:
                o = Literal(res['o']['value'], lang=res['o']['xml:lang'])
            else:
                o = Literal(res['o']['value'])
        g.add((s,p,o))

    return g