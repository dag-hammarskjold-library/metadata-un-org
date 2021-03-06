from rdflib.namespace import SKOS
from rdflib import Namespace
from flask_babel import gettext
from urllib.parse import quote
import boto3
#from metadata.lib.poolparty import PoolParty, Thesaurus

'''
Configuration for the local application.
'''

class CONFIG(object):

    # Get our secrets from AWS SSM
    client = boto3.client('ssm')
    endpoint = client.get_parameter(Name='PoolPartyAPI')['Parameter']['Value']
    username = client.get_parameter(Name='PoolPartyUsername')['Parameter']['Value']
    password = client.get_parameter(Name='PoolPartyPassword')['Parameter']['Value']

    # PoolParty and Linked Data
    project_id = ''

    # App init
    INIT = {
        'title' : 'UN System Names',
        'blueprint_name' : 'unnames',
        'uri_base' : 'http://metadata.un.org/unnames/',
        'include_css' : 'unnames.css',
        'inclide_js' : 'unnames.js',
    }

    SINGLE_CLASSES = {
        'Root': {
            'scheme_uri': 'http://metadata.un.org/unnames',
            'get_properties':[
                'skos:prefLabel',
                'skos:hasTopConcept'
            ],
            'display': [
                'uri',
                'prefLabel'
            ],
            'children': {
                'name':'Goals', 
                'uri': quote('http://www.w3.org/2004/02/skos/core#hasTopConcept'),
                'sort_children_by': 'uri'
            },
            'template': 'unnames_concept.html',
            'id_regex': r'^$'
        },
        'Indicator': {
            'get_properties': [
                'skos:prefLabel',
                'skos:altLabel',
                'skos:notation',
                'skos:broader',
                quote('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
            ],
            'display': [
                'uri',
                'prefLabel',
                'altLabels',
                'notations',
                'broaders',
            ],
            'children':None,
            'template': 'unnames_concept.html',
            'id_regex': r'^C\w{6,6}$'
        },
        'Target': {
            'get_properties': [
                'skos:prefLabel',
                'skos:altLabel',
                'skos:notation',
                'skos:broader',
                quote('http://metadata.un.org/ontology/unnames#hasIndicator'),
                quote('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
            ],
            'display': [
                'uri',
                'prefLabel',
                'altLabels',
                'notations',
                'broaders',
            ],
            'children': {
                'name': 'Indicators',
                'uri': quote('http://metadata.un.org/ontology/sdg#hasIndicator'),
                'sort_children_by': 'uri'
            },
            'template': 'unnames_concept.html',
            'id_regex': r'^\d\.[0-9a-z]$'
        },
        'Goal': {
            'get_properties': [
                'skos:prefLabel',
                'skos:altLabel',
                'skos:notation',
                quote('http://metadata.un.org/ontology/sdg#hasTarget'),
                quote('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
            ],
            'display': [
                'uri',
                'prefLabel',
                'altLabels',
                'notations',
            ],
            'children': {
                'name': 'Targets',
                'uri': quote('http://metadata.un.org/ontology/sdg#hasTarget'),
                'sort_children_by': 'uri'
            },
            'template': 'unnames_concept.html',
            'id_regex': r'^\d{1,2}$'
        }
    }

    # Other stuff
    LANGUAGES = ['en','fr','es']

    KWARGS = {
        'lang': 'en',
        'page': 0,
        'pagination': None,
        'rpp': 20,
        'title': INIT['title'],
        'available_languages': LANGUAGES
    }
