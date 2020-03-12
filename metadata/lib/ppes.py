from elasticsearch import Elasticsearch
from rdflib import ConjunctiveGraph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
from tqdm import tqdm
import importlib, json, requests
import ssl
from elasticsearch.connection import create_ssl_context
#from poolparty import Project

def test_index(datafile):
    graph = ConjunctiveGraph()

    EU = Namespace('http://eurovoc.europa.eu/schema#')
    DC = Namespace('http://purl.org/dc/elements/1.1/')
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    UNBIST = Namespace('http://metadata.un.org/thesaurus/')
    SDG = Namespace('http://metadata.un.org/sdg/')
    SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

    graph.bind('skos', SKOS)
    graph.bind('eu', EU)
    graph.bind('dc', DC)
    graph.bind('dcterms', DCTERMS)
    graph.bind('unbist', UNBIST)
    graph.bind('sdg', SDG)
    graph.bind('sdgo', SDGO)
    
    try:
        graph.parse(datafile, format='ttl')
    except:
        raise

    querystring = querystring = """PREFIX eu: <http://eurovoc.europa.eu/schema#> PREFIX dcterms: <http://purl.org/dc/terms/> select ?uri ?tcode where { ?uri rdf:type skos:Concept . MINUS { ?uri rdf:type eu:MicroThesaurus . } . ?uri dcterms:identifier ?tcode . FILTER( strStarts( ?tcode, 'T')) . }"""

    for uri, tcode in tqdm(graph.query(querystring)):
    #for uri, tcode in graph.query(querystring):
        this_uri = uri
        this_tcode = tcode
        #print(this_uri, this_tcode)
        doc = {"uri": this_uri}
        for lang in CONFIG.LANGUAGES:
            pref_labels = []
            for label in graph.preferredLabel(URIRef(this_uri), lang):
                pref_labels.append(label[1])
            doc.update({"labels_{}".format(lang): pref_labels})

            alt_labels = []
            for label in graph.objects(URIRef(this_uri), SKOS.altLabel):
                if label.language == lang:
                    alt_labels.append(label)
            doc.update({"alt_labels_{}".format(lang): alt_labels})
            doc.update({"tcode": this_tcode}) 

            payload = json.dumps(doc)
            #return(payload)

def rebuild(conn, index_name, index_def, mappings, datafile):
    # delete existing index
    if conn.indices.exists(index_name):
        res = conn.indices.delete(index_name)
    
    # Create new index
    res = conn.indices.create(index=index_name, body=index_def)

    # Apply mappings
    res = con.indices.put_mapping(index=index_name, body=mappings)

    # Load data
    graph = ConjunctiveGraph()

    EU = Namespace('http://eurovoc.europa.eu/schema#')
    DC = Namespace('http://purl.org/dc/elements/1.1/')
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    UNBIST = Namespace('http://metadata.un.org/thesaurus/')
    SDG = Namespace('http://metadata.un.org/sdg/')
    SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

    graph.bind('skos', SKOS)
    graph.bind('eu', EU)
    graph.bind('dc', DC)
    graph.bind('dcterms', DCTERMS)
    graph.bind('unbist', UNBIST)
    graph.bind('sdg', SDG)
    graph.bind('sdgo', SDGO)
    
    try:
        graph.parse(datafile, format='ttl')
    except:
        raise

    querystring = querystring = """PREFIX eu: <http://eurovoc.europa.eu/schema#> PREFIX dcterms: <http://purl.org/dc/terms/> select ?uri ?tcode where { ?uri rdf:type skos:Concept . MINUS { ?uri rdf:type eu:MicroThesaurus . } . ?uri dcterms:identifier ?tcode . FILTER( strStarts( ?tcode, 'T')) . }"""

    for uri, tcode in tqdm(graph.query(querystring)):
    #for uri, tcode in graph.query(querystring):
        this_uri = uri
        this_tcode = tcode
        #print(this_uri, this_tcode)
        doc = {"uri": this_uri}
        for lang in CONFIG.LANGUAGES:
            pref_labels = []
            for label in graph.preferredLabel(URIRef(this_uri), lang):
                pref_labels.append(label[1])
            doc.update({"labels_{}".format(lang): pref_labels})

            alt_labels = []
            for label in graph.objects(URIRef(this_uri), SKOS.altLabel):
                if label.language == lang:
                    alt_labels.append(label)
            doc.update({"alt_labels_{}".format(lang): alt_labels})
            doc.update({"tcode": this_tcode}) 

            payload = json.dumps(doc)

            res = conn.index(index=index_name, body=payload)
            doc = {"uri": this_uri}
