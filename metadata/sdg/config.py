from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
from flask_babel import gettext
from metadata.config import GLOBAL_CONFIG

EU = Namespace('http://eurovoc.europa.eu/schema#')
UNBIST = Namespace('http://metadata.un.org/thesaurus/')
SDG = Namespace('http://metadata.un.org/sdg/')
SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

class ProductionConfig(GLOBAL_CONFIG):
    INIT = {
        'title' : gettext(u'Sustainable Development Goals'),
        'blueprint_name' : 'sdg',
        'uri_base' : 'http://metadata.un.org/sdg/',
        'include_css' : 'sdg.css',
        'include_js' : 'sdg.js',
        'available_languages': GLOBAL_CONFIG.LANGUAGES
    }
    base_uri = 'http://metadata.un.org/sdg'
    local_base_uri = base_uri
    spqarql_endpoint = 'http://localhost:7200/repositories/'
    repository_name = 'SDG-test_core'
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
            'parents': {
                'name': 'sdgo:isSeriesOf',
                'uri': 'http://metadata.un.org/sdg/ontology#isSeriesOf',
                'sort_parents_by': ('http://www.w3.org/2004/02/skos/core#notation','label',8)
            },
            'template': 'sdg_concept.html',
            'id_regex': r'^[A-Z]{2,2}_\w+'
        },
        {
            'name':'Indicator',
            'children': {
                'name': 'sdgo:hasSeries',
                'uri': 'http://metadata.un.org/sdg/ontology#hasSeries',
                'sort_children_by': None
            },
            'parents': {
                'name': 'sdgo:isIndicatorOf',
                'uri': 'http://metadata.un.org/sdg/ontology#isIndicatorOf',
                'sort_parents_by': ('http://www.w3.org/2004/02/skos/core#notation','label',5)
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
            'parents': {
                'name': 'sdgo:isTargetOf',
                'uri': 'http://metadata.un.org/sdg/ontology#isTargetOf',
                'sort_parents_by': ('http://www.w3.org/2004/02/skos/core#notation','label',2)
            },
            'template': 'sdg_concept.html',
            'id_regex': r'^\d{1,2}\.[0-9a-z]{1,2}$'
        },
        {
            'name': 'Goal',
            'children': {
                'name': 'sdgo:hasTarget',
                'uri': 'http://metadata.un.org/sdg/ontology#hasTarget',
                'sort_children_by': ('http://www.w3.org/2004/02/skos/core#notation','label',5)
            },
            'parents': None,
            'template': 'sdg_concept.html',
            'id_regex': r'^\d{1,2}$'
        }
    ]

def get_config():
    # If we had a dev or testing environment, we could return different configs
    return ProductionConfig

Config = get_config()