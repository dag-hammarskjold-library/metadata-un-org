from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode

from metadata.graphs.thesaurus.config import Config

#sparql_endpoint = Config.sparql_endpoint

class Concept(object):

    def __init__(self, uri):
        self.uri = uri

    def graph(self):
        g = Graph()
        for short, ns in Config.namespaces:
            g.bind(short, ns)

        for p in Config.allowed_predicates:
            print(p)