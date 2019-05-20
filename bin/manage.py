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
import importlib



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
        es_con = Elasticsearch(es_uri)
        index_name = CONFIG.INDEX_NAME

        if command == 'create':
            body = CONFIG.INDEX
            res = es_con.indices.create(index=index_name, body=body)
        elif command == 'delete':
            if es_con.indices.exists(index_name):
                res = es_con.indices.delete(index_name)
        elif command == 'build':
            graph = ConjunctiveGraph()
            mapping = CONFIG.MAPPING
            
            try:
                graph.parse(datafile, format='ttl')
            except:
                raise
            res = es_con.indices.put_mapping(index=index_name, doc_type="doc", body=mapping)

            querystring = """ select ?uri where { ?uri rdf:type skos:Concept . }"""

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