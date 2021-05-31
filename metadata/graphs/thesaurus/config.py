from rdflib import RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP

import os
from metadata.config import Config as GlobalConfig

class ProductionConfig(GlobalConfig):
    sparql_endpoint = f"{GlobalConfig.sparql_base}UNBIST_core"

    # Add as many of these as necessary to match the id patterns you have.
    match_classes = [
        {'name': 'Domain', 'regex': r'^[0-9]{2,2}$'},
        {'name': 'MicroThesaurus', 'regex': r'^\d{6,6}$'},
        {'name': 'Concept', 'regex': r'^\d{7,7}$'},
        {'name': 'Concept', 'regex': r'^c_.'},
    ]

    domain_allowed_predicates = [
        RDF.type, SKOS.prefLabel, SKOS.hasTopConcept, DCTERMS.identifier
    ]

    microthesaurus_allowed_predicates = [
        RDF.type, SKOS.prefLabel, SKOS.narrower, SKOS.inScheme, DCTERMS.identifier
    ]

    concept_allowed_predicates = [
        RDF.type,
        SKOS.prefLabel,
        SKOS.altLabel,
        SKOS.hiddenLabel,
        SKOS.historyNote,
        SKOS.note,
        SKOS.scopeNote,
        SKOS.broader,
        SKOS.narrower,
        SKOS.related,
        SKOS.inScheme,
        SKOS.topConceptOf,
        SKOS.hasTopConcept,
        DCTERMS.identifier,
        OWL.deprecated,
        DCTERMS.isReplacedBy
    ]

class DevelopmentConfig(ProductionConfig):
    sparql_endpoint = f"{GlobalConfig.sparql_base}UNBIST-test_core"

def get_config():
    flask_env = os.environ.get('FLASK_ENV', 'development')

    if flask_env == 'production':
        return ProductionConfig
    elif flask_env == 'development':
        return DevelopmentConfig

Config = get_config()