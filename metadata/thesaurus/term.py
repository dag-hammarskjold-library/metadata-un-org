from rdflib import Graph, URIRef, Literal, plugin, RDF
from rdflib.namespace import SKOS
from rdflib.resource import Resource
from rdflib.serializer import Serializer

#>>> g = Graph()
#>>> r = resource.Resource(g,URIRef('http://metadata.un.org/thesaurus/00'))
#>>> r.add(SKOS.prefLabel,Literal(u'UNBIS Thesaurus',lang='en'))
#>>> r.add(RDF.type, SKOS.ConceptScheme)
#>>> print(g.serialize(format='json-ld',indent=4))

g = Graph()

class Term:

    def __init__(self):
        

    def make_rdf(jsdata, class_properties, class_lists):
    # types
    # labels
    # altLabels
    # relationship URIs

    try:
        for rdf_type in jsdata['types']:
            pass
    except KeyError:
        pass

    try:
        for label in jsdata['labels']:
            pass
    except KeyError:
        pass

    try:
        for label in jsdata['altLabels']:
            pass
    except KeyError:
        pass

    try:
        for broader in jsdata['broaders']:
            pass
    except KeyError:
        pass

    try:
        for related in jsdata['relateds']:
            pass
    except KeyError:
        pass

    try:
        for narrower in jsdata['narrowers']:
            pass
    except KeyError:
        pass

    try:
        for scope_note in jsdata['scopeNotes']:
            pass
    except KeyError:
        pass