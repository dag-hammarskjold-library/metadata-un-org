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

    match_classes = [
        {
            'name': 'Root',
            'scheme_uri': 'http://metadata.un.org/sdg',
            'template': 'sdg_index.html',
            'id_regex': r'^$'
        },
        {
            'name': 'Series',
            'children': None,
            'template': 'sdg_concept.html',
            'id_regex': r'^[A-Z]{2,2}_[A-Z]{3,3}_\w+'
        },
        {
            'name':'Indicator',
            'children': {
                'name': 'sdgo:hasSeries',
                'uri': 'http://metadata.un.org/sdg/ontology#hasSeries',
                'sort_children_by': None
            },
            'template': 'sdg_concept.html',
            'id_regex': r'^C\w{6,6}$'
        },
        {
            'name':'Target',
            'children': {
                'name': 'sdgo:hasIndicator',
                'uri': 'http://metadata.un.org/sdg/ontology#hasIndicator',
                'sort_children_by': ('http://www.w3.org/2004/02/skos/core#notation','label',8)
            },
            'template': 'sdg_concept.html',
            'id_regex': r'^\d{1,2}\.[0-9a-z]$'
        },
        {
            'name': 'Goal',
            'children': {
                'name': 'sdgo:hasTarget',
                'uri': 'http://metadata.un.org/sdg/ontology#hasTarget',
                'sort_children_by': ('http://www.w3.org/2004/02/skos/core#notation','label',5)
            },
            'template': 'sdg_concept.html',
            'id_regex': r'^\d{1,2}$'
        }
    ]

    # Other stuff
    #LANGUAGES = ['en','fr','es']
    LANGUAGES = ['en']

    KWARGS = {
        'lang': 'en',
        'page': 0,
        'pagination': None,
        'rpp': 20,
        'title': INIT['title'],
        'available_languages': LANGUAGES
    }
