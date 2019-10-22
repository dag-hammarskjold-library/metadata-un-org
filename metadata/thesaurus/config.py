import boto3, re
from flask_babel import gettext

class CONFIG(object):

    client = boto3.client('ssm')
    connect_string = client.get_parameter(Name='undhl-issu-connect')['Parameter']['Value']

    endpoint = client.get_parameter(Name='PoolPartyAPI')['Parameter']['Value']
    username = client.get_parameter(Name='PoolPartyUsername')['Parameter']['Value']
    password = client.get_parameter(Name='PoolPartyPassword')['Parameter']['Value']
    project_id = '1E033A6C-8F92-0001-A526-1F851B2230F0'

    INIT = {
        'title': gettext(u'UNBIS Thesaurus'),
        'uri_base': 'http://metadata.un.org/thesaurus/',
        #'thesaurus_pattern': '/thesaurus/%s' % PROJECT_ID,
        #'project_pattern': '/projects/%s' % PROJECT_ID    
    }

    available_languages = [
        'ar','zh','en','fr','ru','es'
    ]

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
            'id_regex': r'^\d{7,7}$',
            'template': 'thesaurus_concept.html'
        }
    ]
