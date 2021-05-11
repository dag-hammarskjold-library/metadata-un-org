import boto3, re
from flask_babel import gettext

class CONFIG(object):

    client = boto3.client('ssm')
    connect_string = client.get_parameter(Name='undhl-issu-connect')['Parameter']['Value']

    endpoint = client.get_parameter(Name='PoolPartyAPI')['Parameter']['Value']
    username = client.get_parameter(Name='PoolPartyUsername')['Parameter']['Value']
    password = client.get_parameter(Name='PoolPartyPassword')['Parameter']['Value']
    project_id = '1E033A6C-8F92-0001-A526-1F851B2230F0'

    LANGUAGES = ['ar','zh','en','fr','ru','es']

    INIT = {
        'title': gettext(u'UNBIS Thesaurus'),
        'uri_base': 'http://metadata.un.org/thesaurus/',
        'thesaurus_pattern': '/thesaurus/%s' % project_id,
        'available_languages': LANGUAGES,
        #'project_pattern': '/projects/%s' % PROJECT_ID    
    }

    db_name = 'unbist'

    match_classes = [
        {
            'name': 'Domain',
            'children': [
                {
                    'name': 'Top Concepts',
                    'uri': 'http://www.w3.org/2004/02/skos/core#hasTopConcept',
                    'attributes': [('identifier','http://purl.org/dc/elements/1.1/identifier')],
                    'sort': 'identifier'
                }
            ],
            'id_regex': r'^[0-9]{2,2}$',
            'template': 'thesaurus_domain.html'
        },
        {
            'name': 'MicroThesaurus',
            'children': [
                {
                    'name': 'Narrower Terms',
                    'uri': 'http://www.w3.org/2004/02/skos/core#narrower',
                    'attributes': [],
                    'sort': None
                }
            ],
            'breadcrumb':{
                'self': {
                    'attributes': [
                        ('Identifier','http://purl.org/dc/elements/1.1/identifier'),
                        ('Preferred Term',None)
                    ],
                    'parent': {
                        'name': 'Domain',
                        'uri': 'http://www.w3.org/2004/02/skos/core#inScheme',
                        'attributes': [
                            ('Identifier','http://purl.org/dc/elements/1.1/identifier')
                        ]
                    }
                }
            },
            'id_regex': r'^\d{6,6}$',
            'template': 'thesaurus_microthesaurus.html'
        },
        {
            'name': 'Concept',
            'children': [
                {
                    'name': gettext(u'Broader Terms'),
                    'uri': 'http://www.w3.org/2004/02/skos/core#broader',
                    'attributes': [],
                    'sort': None
                },
                {
                    'name': gettext(u'Narrower Terms'),
                    'uri': 'http://www.w3.org/2004/02/skos/core#narrower',
                    'attributes': [],
                    'sort': None
                },
                {
                    'name': gettext(u'Related Terms'),
                    'uri': 'http://www.w3.org/2004/02/skos/core#related',
                    'attributes': [],
                    'sort': None
                }
            ],
            'id_regex': r'^\d{7,7}$',
            'template': 'thesaurus_concept.html'
        },
        {
            'name': 'Concept',
            'children': [
                {
                    'name': gettext(u'Broader Terms'),
                    'uri': 'http://www.w3.org/2004/02/skos/core#broader',
                    'attributes': [],
                    'sort': None
                },
                {
                    'name': gettext(u'Narrower Terms'),
                    'uri': 'http://www.w3.org/2004/02/skos/core#narrower',
                    'attributes': [],
                    'sort': None
                },
                {
                    'name': gettext(u'Related Terms'),
                    'uri': 'http://www.w3.org/2004/02/skos/core#related',
                    'attributes': [],
                    'sort': None
                }
            ],
            'id_regex': r'^c_.',
            'template': 'thesaurus_concept.html'
        }
    ]

    ELASTICSEARCH_URI = 'http://localhost:9200'
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

    MAPPING = {
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
    

    KWARGS = {
        'lang': 'en',
        'page': 0,
        'pagination': None,
        'rpp': 20,
        'title': INIT['title'],
        'service_available_languages': LANGUAGES
    }