from flask import render_template, redirect, url_for, request, jsonify, abort, json, Response
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
from rdflib import Graph, term, URIRef, Literal, Namespace, RDF
from rdflib.namespace import SKOS
from metadata import cache
from metadata.lib.poolparty import PoolParty, Thesaurus
from metadata.sdg import sdg_app
from metadata.sdg.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es, Pagination
#from metadata.sdg.utils import get_concept, get_labels, build_breadcrumbs, get_schemes, get_concept_list, make_cache_key
from urllib.parse import quote
import re, requests

pool_party = PoolParty(CONFIG.endpoint, CONFIG.project_id, CONFIG.username, CONFIG.password)
thesaurus = Thesaurus(pool_party)

@sdg_app.route('/')
def index():
    uri = CONFIG.SINGLE_CLASSES['Root']['scheme_uri']
    scheme_data = thesaurus.get_concept(concept=uri)

    print(scheme_data)

    if scheme_data is not None:
        return jsonify(scheme_data)