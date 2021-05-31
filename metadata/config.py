import boto3, os
from rdflib import RDF, RDFS, OWL, Namespace
from rdflib import Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP

ssm_client = boto3.client('ssm')

class ProductionConfig(object):    
    dlx_connect = ssm_client.get_parameter(Name='connect-string')['Parameter']['Value']
    
    sparql_base = 'http://localhost:7200/repositories/'

    available_languages = {
        'ar': 'Arabic',
        'zh': 'Chinese',
        'en': 'English',
        'fr': 'French',
        'ru': 'Russian',
        'es': 'Spanish'
    }

    EU = Namespace('http://eurovoc.europa.eu/schema#')
    UNBIST = Namespace('http://metadata.un.org/thesaurus/')
    SDG = Namespace('http://metadata.un.org/sdg/')
    SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

    namespaces = [
        ('skos', SKOS),
        ('eu', EU),
        ('dc', DC),
        ('dcterms', DCTERMS),
        ('unbist', UNBIST),
        ('sdg', SDG),
        ('sdgo', SDGO),
        ('foaf', FOAF),
        ('doap', DOAP),
        ('rdf', RDF),
        ('rdfs', RDFS),
        ('owl', OWL)
    ]

    jsonld_context = dict((s,Namespace(str(n))) for s,n in namespaces)

    global_kwargs = {
        'lang': 'en',
        'site_available_languages': available_languages.keys()
    }

class DevelopmentConfig(ProductionConfig):    
    dlx_connect = ssm_client.get_parameter(Name='dev-connect-string')['Parameter']['Value']

''' To do:
class TestConfig(ProductionConfig):
    dlx_connect = None
'''


def get_config():
    flask_env = os.environ.get('FLASK_ENV', 'development')

    if flask_env == 'production':
        return ProductionConfig
    elif flask_env == 'development':
        return DevelopmentConfig


Config = get_config()