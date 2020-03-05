from flask import render_template, redirect, url_for, request, jsonify, abort, json
from mongoengine import connect
from elasticsearch import Elasticsearch
from metadata import cache
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language
from metadata.lib.ppmdb import Concept, Label, Relationship, reload_concept
from metadata.lib.poolparty import PoolParty, Thesaurus
import re, requests, ssl

# Common set of kwargs to return, just in case
#return_kwargs = {
#    **KWARGS,
#    **GLOBAL_KWARGS
#}


INIT = CONFIG.INIT
#SINGLE_CLASSES = CONFIG.SINGLE_CLASSES
LANGUAGES = CONFIG.LANGUAGES
KWARGS = CONFIG.KWARGS
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS

connect(host=CONFIG.connect_string, db=CONFIG.db_name, ssl_cert_reqs=ssl.CERT_NONE)
pool_party = PoolParty(CONFIG.endpoint, CONFIG.project_id, CONFIG.username, CONFIG.password)
thesaurus = Thesaurus(pool_party)

def get_or_update(uri, languages=['en']):
    '''
    First try getting from the database. If that fails, reload from PoolParty
    '''
    try:
        concept = Concept.objects.get(uri=uri)
        return concept
    except:
        reload_true = reload_concept(uri, thesaurus, languages)
        if reload_true:
            concept = Concept.objects.get(uri=uri)
            return concept
        else:
            return None

def replace_concept(uri):
    print(uri)
    try:
        reload_concept(uri, thesaurus)
        return True
    except:
        return False

def reindex_concept(concept):
    es_con = Elasticsearch(CONFIG.ELASTICSEARCH_URI)
    index_name = CONFIG.INDEX_NAME
    doc = {"uri": concept.uri}
    #identifiers = concept.get_property_values_by_predicate('http://purl.org/dc/elements/1.1/identifier')
    #tcode = next(filter(lambda x: re.match(r'^T',x['label']), identifiers),None)
    for lang in CONFIG.LANGUAGES:
        pref_labels = []
        for label in concept.get_labels('pref_labels',lang):
            pref_labels.append(label.label)
        doc.update({"labels_{}".format(lang): pref_labels})

        alt_labels = []
        for label in concept.get_labels('alt_labels',lang):
            alt_labels.append(label.label)
        doc.update({"alt_labels_{}".format(lang): alt_labels})

        #if tcode is not None:
        #    doc.update({"tcode": tcode}) 
        

        payload = json.dumps(doc)

        print(doc)

        res = es_con.index(index=index_name, doc_type='doc', body=payload)
        doc = {"uri": concept.uri}

    return True

def unindex_concept(uri):
    es_con = Elasticsearch(CONFIG.ELASTICSEARCH_URI)
    index_name = CONFIG.INDEX_NAME
    