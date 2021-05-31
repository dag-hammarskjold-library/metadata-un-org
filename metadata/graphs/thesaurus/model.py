from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
import requests, json

from metadata.graphs.thesaurus.config import Config

sparql_endpoint = Config.sparql_endpoint

def build_graph(uri, allowed_predicates):
    g = Graph()
    for short, ns in Config.namespaces:
        g.bind(short, ns)

    triple_q = f"""SELECT ?s ?p ?o {{ <{uri}> ?p ?o }}"""
    params = {
        'query': triple_q
    }
    headers = {
        'accept': 'application/json'
    }
    response = requests.get(sparql_endpoint, headers=headers, params=params)
    json_data = json.loads(response.text)
    for res in json_data['results']['bindings']:
        s = URIRef(uri)
        p = URIRef(res['p']['value'])
        o = None
        if p in allowed_predicates:
            if res['o']['type'] == 'uri':
                o = URIRef(res['o']['value'])
            elif res['o']['type'] == 'literal':
                if 'xml:lang' in res['o']:
                    o = Literal(res['o']['value'], lang=res['o']['xml:lang'])
                else:
                    o = Literal(res['o']['value'])
            g.add((s,p,o))
    return g


class Concept(object):
    def __init__(self, uri, allowed_predicates=[]):
        self.uri = uri
        self.allowed_predicates = Config.concept_allowed_predicates
        self.graph = build_graph(self.uri, self.allowed_predicates)
        
class MicroThesaurus(object):
    def __init__(self, uri, allowed_predicates=[]):
        self.uri = uri
        self.allowed_predicates = Config.microthesaurus_allowed_predicates
        self.graph = build_graph(self.uri, self.allowed_predicates)


class Domain(object):
    def __init__(self, uri, allowed_predicates=[]):
        self.uri = uri
        self.allowed_predicates = Config.domain_allowed_predicates
        self.graph = build_graph(self.uri, self.allowed_predicates)

class Breadcrumb(object):
    
    pass

class Thesaurus(object):
    def __init__(self, base_uri, domain_type):
        self.base_uri = base_uri

    def graph(self):
        g = Graph()