from rdflib.namespace import SKOS
from rdflib import Namespace
from flask_babel import gettext
from urllib.parse import quote
from gettext import gettext
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
    connect_string = client.get_parameter(Name='undhl-issu-connect')['Parameter']['Value']

    db_name = 'sdg'

    # PoolParty and Linked Data
    project_id = '1E14D161-1692-0001-C5E4-4AF2A7E36A50'

    # App init
    INIT = {
        'title' : 'Sustainable Development Goals',
        'blueprint_name' : 'sdg',
        'uri_base' : 'http://metadata.un.org/sdg/',
        'include_css' : 'sdg.css',
        'include_js' : 'sdg.js',
    }

    SINGLE_CLASSES = {
        'Root': {
            'scheme_uri': 'http://metadata.un.org/sdg',
            'get_properties': [
                'skos:prefLabel',
                #quote('http://www.w3.org/2004/02/skos/core#hasTopConcept')
            ],
            'template': 'sdg_index.html',
            'id_regex': r'^$'
        },
        'Indicator': {
            'get_properties': [
                'skos:prefLabel',
                'skos:altLabel',
                'skos:notation',
                'skos:broader',
                quote('http://metadata.un.org/sdg/ontology#hasIndicator'),
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
            'template': 'sdg_concept.html',
            'id_regex': r'^C\w{6,6}$'
        },
        'Target': {
            'get_properties': [
                'skos:prefLabel',
                'skos:altLabel',
                'skos:notation',
                'skos:broader',
                quote('http://metadata.un.org/sdg/ontology#hasIndicator'),
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
                'uri': quote('http://metadata.un.org/sdg/ontology#hasIndicator'),
                'sort_children_by': 'uri'
            },
            'template': 'sdg_concept.html',
            'id_regex': r'^\d\.[0-9a-z]$'
        },
        'Goal': {
            'get_properties': [
                'skos:prefLabel',
                'skos:altLabel',
                'skos:notation',
                quote('http://metadata.un.org/sdg/ontology#hasTarget'),
                quote('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
            ],
            'display': [
                gettext(u'uri'),
                gettext(u'prefLabel'),
                gettext(u'altLabels'),
                gettext(u'notations'),
            ],
            'children': {
                'name': gettext(u'Targets'),
                'uri': quote('http://metadata.un.org/sdg/ontology#hasTarget'),
                'sort_children_by': 'uri'
            },
            'template': 'sdg_concept.html',
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
