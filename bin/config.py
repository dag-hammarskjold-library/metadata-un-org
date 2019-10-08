LANGUAGES = ['ar','zh','en','fr','ru','es']

ELASTICSEARCH_URI = "https://vpc-unbist-u33q3473bjc4ywopwx5byguxuq.us-east-1.es.amazonaws.com"
INDEX_NAME = 'unbis_thesaurus_dev'
PROXY_ENDPOINT = 'http://metadata.un.org:8080/_reindex'

INDEX = {
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
                    "max_gram": 40,
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
        "tcode": {"type": "text"},
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
