from typing import Type
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP, XSD
from rdflib.term import URIRef, Literal, BNode

def graph_concept(concept):
    # takes a Concept object as argument, returns a Graph
    g = Graph()
    EU = Namespace('http://eurovoc.europa.eu/schema#')
    #DC = Namespace('http://purl.org/dc/elements/1.1/')
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    UNBIST = Namespace('http://metadata.un.org/thesaurus/')
    SDG = Namespace('http://metadata.un.org/sdg/')
    SDGO = Namespace('http://metadata.un.org/sdg/ontology#')
    #PPU = Namespace('https://unlibrary.poolparty.biz/user/')

    g.bind('skos', SKOS)
    g.bind('eu', EU)
    #g.bind('dc', DC)
    g.bind('dcterms', DCTERMS)
    g.bind('unbist', UNBIST)
    g.bind('sdg', SDG)
    g.bind('sdgo', SDGO)
    #g.bind('ppu', PPU)

    '''
    jsonld_context = {
        'skos': SKOS,
        'eu': EU,
        #'dc': DC,
        'dcterms': DCTERMS,
        #'unbist': UNBIST,
        #'sdg': SDG,
        'sdgo': SDGO,
        #'ppu': PPU
    }
    '''

    jsonld_context = {
        
    }

    skip_list = [
        'http://purl.org/dc/terms/contributor',
        'http://purl.org/dc/terms/creator'
    ]

    for rdfp in concept.rdf_properties:       
        for o in rdfp.object:
            if 'label' in o:
                if 'language' in o:
                    g.add((
                        URIRef(concept.uri),
                        URIRef(rdfp.predicate), 
                        Literal(o['label'], lang=o['language'])
                    ))
                elif 'datatype' in o:
                    g.add((
                        URIRef(concept.uri),
                        URIRef(rdfp.predicate), 
                        Literal(o['label'], datatype=URIRef(o['datatype']['uri']))
                    ))
                else:
                    g.add((
                        URIRef(concept.uri),
                        URIRef(rdfp.predicate), 
                        Literal(o['label'], datatype=XSD.string)
                    ))
            else:
                g.add((URIRef(concept.uri),URIRef(rdfp.predicate), URIRef(o['uri'])))
    return g, jsonld_context