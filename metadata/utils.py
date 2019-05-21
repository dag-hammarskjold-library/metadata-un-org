from flask import request, jsonify
from math import ceil

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

class Pagination:
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return int(self.page) > 1

    @property
    def has_next(self):
        return int(self.page) < int(self.pages)

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > int(self.page) - int(left_current) - 1 and
                num < int(self.page) + int(right_current)) or \
               num > int(self.pages) - int(right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num