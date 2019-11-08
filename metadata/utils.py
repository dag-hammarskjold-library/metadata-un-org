from flask import request, jsonify, json
from math import ceil
from urllib.parse import unquote
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
import re, requests, pprint

def fetch_external_label(uri, language='en', mimetype='application/rdf+xml'):
    '''
    This function looks at a target URI and attempts to resolve the label.
    It assumes you know what content type you're looking for and that the 
    target service can return objects we can work with...

    You can access the function synchronously or asynchronously as you see fit.
    '''
    # put this in config probably
    whitelisted_sources = [
        {'name':'EuroVoc', 'uri': 'http://eurovoc.europa.eu'},
        {'name':'UNBIS Thesaurus', 'uri': 'http://metadata.un.org/thesaurus'},
        {'name':'SDG', 'uri': 'http://metadata.un.org/sdg'}
    ]

    #print(uri,language,mimetype)

    this_source = next(filter(lambda x: re.match(x['uri'],uri),whitelisted_sources),None)
    if this_source:
        this_doc = requests.get(uri,headers={'accept':mimetype}).text
        g = Graph()
        g.parse(data=this_doc, format='xml')
        try:
            this_label = g.preferredLabel(URIRef(uri), lang=language)[0][1]
        except:
            this_label = g.preferredLabel(URIRef(uri), lang='en')[0][1]
        return_data = {'label': this_label, 'uri': uri, 'source': this_source}
        #print(return_data)
        return return_data
    else:
        #print("None")
        return None

    

def get_preferred_language(request, return_kwargs):
    print(return_kwargs)
    lang = request.args.get('lang','en')
    try:
        available_langs = return_kwargs['service_available_languages']
    except KeyError:
        available_langs = return_kwargs['available_languages']
    if lang in available_langs:
        return_kwargs['lang'] = lang
    else:
        return_kwargs['lang'] = 'en'
    return return_kwargs

def write_to_index(es_connection, index_name, payload):
    res = es_connection.index(index=index_name, doc_type='doc', body=payload)
    return res

def query_es(connection, index_name, query, lang, max_hits):
    """
    Match against the prefLabel and altLabel entries for the preferred language.
    Boost the prefLabel entry.
    This, of course, assumes Elasticsearch.
    """
    print(connection)
    special_chars = '+|"-\*()~'
    #special_chars = r'"'

    #print(query)
    #print(unquote(query))

    if any((c in special_chars) for c in query):
        #print(json.dumps(query))
        dsl_q = """
        {
            "query": {
                "simple_query_string": {
                    "query": %s,
                    "fields": [ "labels_%s^3", "alt_labels_%s" ],
                    "flags": "ALL"
                }
            },
            "highlight": {
                    "fields": {
                        "labels_%s": {"type": "plain"}, 
                        "alt_labels_%s": {"type": "plain"} 
                    },
                    "pre_tags": ["<b>"],
                    "post_tags": ["</b>"]
                }
        }
        """ % (json.dumps(query), lang, lang, lang, lang)
    else:
        dsl_q = """
            {
                "query": {
                    "multi_match": {
                        "query": "%s",
                        "fields": [ "labels_%s^3", "alt_labels_%s" ]
                    }
                },
                "highlight": {
                    "fields": {
                        "labels_%s": {"type": "plain"}, 
                        "alt_labels_%s": {"type": "plain"} 
                    },
                    "pre_tags": ["<b>"],
                    "post_tags": ["</b>"]
                }
            }""" % (query, lang, lang, lang, lang)

    #print(dsl_q)
    match = connection.search(index=index_name, body=dsl_q, size=max_hits)
    pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(match)
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
