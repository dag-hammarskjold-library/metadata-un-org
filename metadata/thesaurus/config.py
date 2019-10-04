from rdflib.namespace import SKOS
from rdflib import Namespace
from flask_babel import gettext
import boto3

'''
Configuration for the local application.
'''

class CONFIG:
    # PoolParty and Linked Data

    # Get our secrets from AWS SSM
    client = boto3.client('ssm')
    PROJECT_ID = '1E033A6C-8F92-0001-A526-1F851B2230F0'

    API = {
        'source': client.get_parameter(Name='PoolPartyAPI')['Parameter']['Value'],
        'user': client.get_parameter(Name='PoolPartyUsername')['Parameter']['Value'],
        'password': client.get_parameter(Name='PoolPartyPassword')['Parameter']['Value']
    }

    INIT = {
        'title': gettext(u'UNBIS Thesaurus'),
        'uri_base': 'http://metadata.un.org/thesaurus/',
        'thesaurus_pattern': '/thesaurus/%s' % PROJECT_ID,
        'project_pattern': '/projects/%s' % PROJECT_ID    
    }

    EU = Namespace('http://eurovoc.europa.eu/schema#')

    SINGLE_CLASSES = {
        'Root': {
            'uri': 'http://metadata.un.org/thesaurus/00',
            'get_properties': ['all'],
            'display_properties': [
                #'prefLabel',
                'http://purl.org/dc/terms/hasPart',
            ],
            'child_accessor_property': 'http://purl.org/dc/terms/hasPart',
            'child_sort_key': 'dc:identifier',
            'template': 'thesaurus_index.html',
            'id_regex': r'^00$',
        },
        'Concept': {
            'get_properties': [
                'rdf:type',
                'skos:ConceptScheme',
                'skos:prefLabel',
                'skos:altLabel',
                'skos:scopeNote',
                'skos:broader',
                'skos:related',
                'skos:narrower',
                'skos:exactMatch'
            ],
            'display_properties': [
                #'prefLabel',
                'broaders',
                'relateds',
                'narrowers'
            ],
            'child_sort_key': 'prefLabel',
            'template': 'thesaurus_concept.html',
            'id_regex': r'^\d{7,7}$'
        },
        'MicroThesaurus': {
            'get_properties': [
                'rdf:type',
                'skos:ConceptScheme',
                'skos:prefLabel',
                'skos:narrower',
                'dc:identifier'
            ],
            'display_properties': [
                #'prefLabel',
                'narrowers'
            ],
            'lists': ['narrowers'],
            'child_sort_key': 'prefLabel',
            'template': 'thesaurus_microthesaurus.html',
            'id_regex': r'^\d{6,6}$'
        },
        'Domain': {
            'get_properties': [
                'rdf:type',
                'skos:prefLabel',
                'skos:hasTopConcept',
                'dc:identifier',
            ],
            'display_properties': [
                'http://www.w3.org/2004/02/skos/core#hasTopConcept',
            ],
            'child_accessor_property':'skos:hasTopConcept',
            'child_sort_key': 'dc:identifier',
            'lists': ['childconcepts'],
            'template': 'thesaurus_domain.html',
            'id_regex': r'^\d{2,2}$'
        }
    }

    # Elasticsearch
    # The URI or connection details perhaps belong in the global config.
    ELASTICSEARCH_URI = client.get_parameter(Name='ElasticSearchURI')['Parameter']['Value']
    INDEX_NAME = 'unbis_thesaurus'

    THESAURUS_INDEX = {
        "settings": {
            "index": {
                "number_of_shards": 3
            },
            "analysis": {
                "analyzer": {
                    "autocomplete": {
                        "tokenizer": "autocomplete",
                        "filter": [
                            "lowercase"
                        ]
                    },
                    "autocomplete_search": {
                        "tokenizer": "lowercase"
                    }
                },
                "tokenizer": {
                    "autocomplete": {
                        "type": "edge_ngram",
                        "min_gram": 3,
                        "max_gram": 10,
                        "token_chars": [
                            "letter",
                            "digit"
                        ]
                    }
                }
            }
        }
    }

    THESAURUS_MAPPING = {
        "properties": {
            "uri": {"type": "text", "index": "false"},
            "labels_ar": {"type": "text", "analyzer": "arabic"},
            "labels_zh": {"type": "text", "analyzer": "chinese"},
            "labels_en": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
            "labels_fr": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
            "labels_ru": {"type": "text", "analyzer": "russian"},
            "labels_es": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
            "alt_labels_ar": {"type": "text", "analyzer": "arabic"},
            "alt_labels_zh": {"type": "text", "analyzer": "chinese"},
            "alt_labels_en": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
            "alt_labels_fr": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
            "alt_labels_ru": {"type": "text", "analyzer": "russian"},
            "alt_labels_es": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
        }
    }


    # Other stuff
    LANGUAGES = ['ar','zh','en','fr','ru','es']

    KWARGS = {
        'lang': 'en',
        'page': 0,
        'pagination': None,
        'rpp': 20,
        'title': INIT['title']
    }
