from flask import request, jsonify

def get_preferred_language(request, return_kwargs):
    lang = request.args.get('lang','en')
    return_kwargs['lang'] = lang
    return return_kwargs

def write_to_index(es_connection, index_name, payload):
    es_connection.index(index=index_name, doc_type='doc', body=payload)