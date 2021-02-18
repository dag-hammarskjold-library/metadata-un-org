import boto3
import os

client = boto3.client('ssm')

class ProductionConfig(object):
    context = 'production'
    
    LANGUAGES = {
        'ar': 'Arabic',
        'zh': 'Chinese',
        'en': 'English',
        'fr': 'French',
        'ru': 'Russian',
        'es': 'Spanish'
    }

    GLOBAL_KWARGS = {
        'lang': 'en',
        'site_available_languages': ['ar','zh','en','fr','ru','es']
    }

    CACHE_KEY = client.get_parameter(Name='metadata_cache_key')['Parameter']['Value']
    CACHE_SERVERS = [client.get_parameter(Name='ElastiCacheServer')['Parameter']['Value']]
    connect_string = client.get_parameter(Name='mdu_connect')['Parameter']['Value']
    ELASTICSEARCH_URI = 'http://localhost:9200'

class DevelopmentConfig(ProductionConfig):
    context = 'development'
    onnect_string = client.get_parameter(Name='dev_mdu_connect')['Parameter']['Value']

def get_config():
    mdu_env = os.environ.setdefault('MDU_ENV', 'development')
    if mdu_env == 'production':
        return ProductionConfig
    elif mdu_env == 'development':
        return DevelopmentConfig
    else:
        return DevelopmentConfig

GLOBAL_CONFIG = get_config()