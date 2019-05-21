from flask import request, jsonify

def get_preferred_language(request, return_kwargs):
    lang = request.args.get('lang','en')
    return_kwargs['lang'] = lang
    return return_kwargs

def write_to_index(es_connection, index_name, payload):
    es_connection.index(index=index_name, doc_type='doc', body=payload)

def query_es(connection, index_name, query, lang, max_hits):
    """
    Match against the prefLabel and altLabel entries for the preferred language.
    Boost the prefLabel entry.
    This, of course, assumes Elasticsearch.
    """

    dsl_q = """
        {
            "query": {
                "multi_match": {
                    "query": "%s",
                    "fields": [ "labels_%s^3", "alt_labels_%s" ]
                }
            }
        }""" % (query, lang, lang)

    match = connection.search(index=index_name, body=dsl_q, size=max_hits)
    return match