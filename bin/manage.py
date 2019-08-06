#!/bin/env python
"""
metadata.un.org manager tool

Usage:
    manage.py [-h] <subsystem> <command> -c <config> [-d <datafile>]

Options:
    -h --help                   Shows this help text.
    -c --config <config>        config.py file location.
    -d --datafile <datafile>    A ttl formatted data file.
"""

from docopt import docopt
from elasticsearch import Elasticsearch
from rdflib import plugin, ConjunctiveGraph, Namespace, Literal, URIRef
from rdflib.namespace import SKOS 
from tqdm import tqdm
import importlib, json



if __name__ == '__main__':
    arguments = docopt(__doc__,version='manage 1.0')

    config = arguments['--config']
    command = arguments['<command>']
    subsystem = arguments['<subsystem>']
    datafile = arguments['--datafile']

    # parse the config file
    try:
        CONFIG = importlib.import_module(config)
    except:
        raise

    if subsystem == 'index':
        es_uri = CONFIG.ELASTICSEARCH_URI
        index_name = CONFIG.INDEX_NAME
        proxy_endpoint = CONFIG.PROXY_ENDPOINT

        if command == 'create':
            es_con = Elasticsearch(es_uri)
            body = CONFIG.INDEX
            res = es_con.indices.create(index=index_name, body=body)
        elif command == 'delete':
            es_con = Elasticsearch(es_uri)
            if es_con.indices.exists(index_name):
                res = es_con.indices.delete(index_name)
        elif command == 'prepare':
            es_con = Elasticsearch(es_uri)
            mapping = CONFIG.MAPPING
            res = es_con.indices.put_mapping(index=index_name, doc_type="doc", body=mapping)

        elif command == 'build':
            es_con = Elasticsearch(es_uri)
            graph = ConjunctiveGraph()
            
            try:
                graph.parse(datafile, format='ttl')
            except:
                raise

            querystring = """PREFIX eu: <http://eurovoc.europa.eu/schema#> select ?uri where { ?uri rdf:type skos:Concept . MINUS { ?uri rdf:type eu:MicroThesaurus . } }"""

            for uri in tqdm(graph.query(querystring)):
                this_uri = uri[0]
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

                    payload = json.dumps(doc)

                    res = es_con.index(index=index_name, doc_type='doc', body=payload)
                    doc = {"uri": this_uri}

        elif command == 'proxy-build':
            ''' Run the indexing script from a remote server using a Flask route to proxy requests. Best for when this app is deployed in low resource environments.'''
            graph = ConjunctiveGraph()
            
            try:
                graph.parse(datafile, format='ttl')
            except:
                raise

            querystring = """PREFIX eu: <http://eurovoc.europa.eu/schema#> select ?uri where { ?uri rdf:type skos:Concept . MINUS { ?uri rdf:type eu:MicroThesaurus . } }"""

            for uri in tqdm(graph.query(querystring)):
                this_uri = uri[0]
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

                    payload = json.dumps(doc)

                    #res = es_con.index(index=index_name, doc_type='doc', body=payload)
                    res = requests.post(proxy_endpoint, data={'body':payload, 'es_uri':es_uri, 'index_name':index_name, 'key':GLOBAL_CONFIG.CACHE_KEY})
                    doc = {"uri": this_uri}
