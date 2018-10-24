from rdflib.namespace import SKOS
from rdflib import Namespace

'''
Configuration for the local application.
'''

EU = Namespace('http://eurovoc.europa.eu/schema#')

LIST_CLASSES = {
    'Domains': {
        'rdf_type': EU.Domain,
        'template': 'domains_list.html',
        'pagination': 0
    },
    'MicroThesauri': {
        'rdf_type': EU.MicroThesaurus,
        'template': 'microthesauri_list.html',
        'pagination': 25
    }
}

SINGLE_CLASSES = {
    'Concept': {
        'rdf_type': SKOS.Concept,
        'template': 'concept.html'
    },
    'Domain': {
        'rdf_type': EU.Domain,
        'template': 'domain.html'
    },
    'MicroThesaurus': {
        'rdf_type': EU.MicroThesaurus,
        'template': 'microthesaurus.html'
    }
}