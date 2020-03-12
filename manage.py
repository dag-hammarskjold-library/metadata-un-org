from elasticsearch import Elasticsearch
from rdflib import ConjunctiveGraph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
from tqdm import tqdm
import importlib, json, requests
import ssl
from elasticsearch.connection import create_ssl_context
from metadata.lib.poolparty import PoolParty, Project
from metadata.lib.ppes import rebuild
from flask_script import Manager
from flask import Flask

from metadata import app

def create_app(blueprint='thesaurus'):
    config = importlib.import_module('metadata.%s.config' % blueprint)
    app.config.from_object(config.CONFIG)
    #print(config.CONFIG)
    return app

manager = Manager(create_app())
manager.add_option('-b', '--blueprint', required=False)

@manager.command
def test():
    print('Testing the setup. If this generates any errors, you have something misconfigured.')
    print(app.config.get('ELASTICSEARCH_URI'))
    #print(manager._options[0])

@manager.command
def rebuild_elasticsearch():
    print(app.config)
    es_uri = app.config.get('ELASTICSEARCH_URI')
    index_name = app.config.get('INDEX_NAME')
    endpoint = app.config.get('ENDPOINT')
    project_id = app.config.get('PROJECT_ID')
    username = app.config.get('USERNAME')
    password = app.config.get('PASSWORD')
    index_def = app.config.get(manager.option)

    #print(es_uri, index_name, endpoint, project_id, username, password)
    
    pool_party = PoolParty(endpoint, project_id, username, password)
    project = Project(pool_party)

    project_data = project.export(format='ttl',export_modules=['concepts'],pretty_print='false')

    es_con = Elasticsearch(es_uri)

'''
    try:
        rebuild(es_con, index_name, )
'''

if __name__ == '__main__':
    manager.run()