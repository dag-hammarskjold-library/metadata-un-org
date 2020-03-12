#!/bin/env python
"""
metadata.un.org manager tool for reloading data

Usage:
    manage.py [-h] <subsystem> <command> -c <config> [-d <datafile>]

Options:
    -h --help                   Shows this help text.
    -c --config <config>        config.py file location.
    -d --datafile <datafile>    A ttl formatted data file.
"""

from docopt import docopt
from elasticsearch import Elasticsearch
from rdflib import ConjunctiveGraph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
from tqdm import tqdm
import importlib, json, requests
import ssl
from elasticsearch.connection import create_ssl_context

context = create_ssl_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE


if __name__ == '__main__':
    arguments = docopt(__doc__,version='manage 1.0')

    config = arguments['--config']
    command = arguments['<command>']
    subsystem = arguments['<subsystem>']
    datafile = arguments['--datafile']

    # parse the config file
    try:
        CONFIG = importlib.import_module(config).CONFIG
    except:
        raise

    if subsystem == 'search':
        es_uri = CONFIG.ELASTICSEARCH_URI
        es_con = Elasticsearch(es_uri, ssl_context=context)
        index_name = CONFIG.INDEX_NAME

        if command == 'test':
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
                    print(payload)

            #print(graph.serialize(format='ttl'))

        if command == 'create':
            body = CONFIG.INDEX
            res = es_con.indices.create(index=index_name, body=body)

        elif command == 'delete':
            if es_con.indices.exists(index_name):
                res = es_con.indices.delete(index_name)

        elif command == 'prepare':
            mapping = CONFIG.MAPPING
            res = es_con.indices.put_mapping(index=index_name, body=mapping)

        elif command == 'build':
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

            #querystring = """PREFIX eu: <http://eurovoc.europa.eu/schema#> select ?uri where { ?uri rdf:type skos:Concept . MINUS { ?uri rdf:type eu:MicroThesaurus . } }"""
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

                    res = es_con.index(index=index_name, body=payload)
                    doc = {"uri": this_uri}
