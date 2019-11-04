import boto3

class GLOBAL_CONFIG:
    client = boto3.client('ssm')
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
        'available_languages': ['ar','zh','en','fr','ru','es']
    }

    CACHE_KEY = client.get_parameter(Name='metadata_cache_key')['Parameter']['Value']
    CACHE_SERVERS = [client.get_parameter(Name='ElastiCacheServer')['Parameter']['Value']]