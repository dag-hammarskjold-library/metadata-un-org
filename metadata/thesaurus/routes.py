from flask import render_template, redirect, url_for, request, jsonify, abort, json
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
from metadata import cache
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language, query_es, Pagination
from metadata.thesaurus.utils import get_concept, get_labels, build_breadcrumbs, get_schemes, get_concept_list, make_cache_key
import re, requests

# This should be deprecated/refactored
API = CONFIG.API
INIT = CONFIG.INIT
SINGLE_CLASSES = CONFIG.SINGLE_CLASSES
LANGUAGES = CONFIG.LANGUAGES
KWARGS = CONFIG.KWARGS
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS

# Common set of kwargs to return in all cases. 
return_kwargs = {
    **KWARGS,
    **GLOBAL_KWARGS
}

# Other Init
ES_CON = Elasticsearch(CONFIG.ELASTICSEARCH_URI)

@thesaurus_app.route('/')
@cache.cached(timeout=None, key_prefix=make_cache_key)
def index():
    '''
    This should return a landing page for the thesaurus application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    #print(cache.get(request.path))

    get_preferred_language(request, return_kwargs)
    this_sc = SINGLE_CLASSES['Root']
    uri = this_sc['uri']
    return_properties = ",".join(this_sc['get_properties'])
    api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], uri, return_properties, return_kwargs['lang']
    )

    #print(api_path)
    return_data = get_concept(uri, api_path, this_sc, return_kwargs['lang'])
    #print(return_data)

    return render_template('thesaurus_index.html', data=return_data, **return_kwargs)

@thesaurus_app.route('/T<id>')
def get_by_tcode(id):
    this_id = "T" + id
    id_regex = r'^T\d+'
    p = re.compile(id_regex)
    if not p.match(this_id):
        abort(500)
    dsl_q = '''{ "query": { "match": { "tcode": "%s" } } }''' % this_id
				
    try:
        this_uri = ES_CON.search(index=CONFIG.INDEX_NAME, body=dsl_q)['hits']['hits'][0]['_source']['uri']
    except IndexError:
        abort(404)
    return jsonify({"id": this_id, "uri": this_uri})

@thesaurus_app.route('/<id>')
@cache.cached(timeout=None, key_prefix=make_cache_key)
def get_by_id(id):
    '''
    This should return the landing page for a single instance of
    a record, such as an individual Concept, Domain, or MicroThesaurus

    Positive matching is done against a whitelist of RDF Types 
    and id regular expressions patterns as definied in 
    metadata.thesaurus.config. This is intended to pre-screen 
    user input and reject anything that doesn't fit a strict 
    pattern.
    '''
    
    if id == '00':
        return redirect('/')
    get_preferred_language(request, return_kwargs)

    for single_class in SINGLE_CLASSES:
        this_sc = SINGLE_CLASSES[single_class]
        p = re.compile(this_sc['id_regex'])
        if p.match(id):
            #print(this_sc)
            uri = INIT['uri_base'] + id
            return_properties = ",".join(this_sc['get_properties'])
            api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
                API['source'], INIT['thesaurus_pattern'], uri, return_properties, return_kwargs['lang']
            )
            #print(api_path)
            return_data = get_concept(uri, api_path, this_sc, return_kwargs['lang'])
            #print(return_data)
            if return_data is None:
                return render_template('404.html', **return_kwargs), 404
            return render_template(this_sc['template'], **return_kwargs, data=return_data, subtitle=return_data['prefLabel'])
        else:
            next
            
    return render_template('404.html', **return_kwargs), 404

@thesaurus_app.route('/categories')
@cache.cached(timeout=None, key_prefix=make_cache_key)
def categories():
    '''
    This route returns a list of the categories (concept schemes) in the service.
    '''
    get_preferred_language(request, return_kwargs)
    api_path = '%s%s/schemes?language=%s' % (
        API['source'], INIT['thesaurus_pattern'], return_kwargs['lang']
    )
    
    #print(api_path)
    return_data = get_schemes(api_path)
    if return_data is None:
        return render_template('404.html', **return_kwargs, subtitle=gettext('Not Found')), 404

    return render_template('thesaurus_categories.html', data=return_data, **return_kwargs, subtitle=gettext('Browse Concepts'))

@thesaurus_app.route('/alphabetical', defaults={'page': 1})
@thesaurus_app.route('/alphabetical/page/<int:page>')
#@thesaurus_app.route('/alphabetical')
#@cache.cached(timeout=None, key_prefix=make_cache_key)
def alphabetical(page):
    '''
    This returns an alphabetical list of terms, or what passes for a 
    logical ordering by label in the target language.

    Maybe this should be done asynchronously?
    '''
    get_preferred_language(request, return_kwargs)

    if return_kwargs['lang'] == 'zh':
        return render_template('thesaurus_alphabetical.html', data=url_for('static',filename='zh_sorted.json'),  **return_kwargs, subtitle=gettext('Browse Alphabetically'))

    api_path = '%s%s/schemes?language=%s' % (
        API['source'], INIT['thesaurus_pattern'], return_kwargs['lang']
    )
    concept_schemes = get_schemes(api_path)
    this_data = []
    for cs in concept_schemes:
        subtree_path = '%s%s/subtree?root=%s&language=%s' % (
            API['source'], INIT['thesaurus_pattern'], cs['uri'], return_kwargs['lang']
        )
        concepts = get_concept_list(subtree_path)
        for c in concepts:
            for n in c['narrowers']:
                try:
                    #print(n['concept'])
                    if n['concept'] not in this_data:
                        this_data.append(n['concept'])
                except TypeError:
                    pass

    return_data = sorted(this_data, key=lambda k: k['prefLabel'])

    return render_template('thesaurus_alphabetical.html', data=return_data, **return_kwargs, subtitle=gettext('Browse Alphabetically'))

@thesaurus_app.route('/new')
def term_updates():
    get_preferred_language(request, return_kwargs)
    api_path = '%shistory/%s?fromTime=%s&lang=%s' % (
        API['source'], INIT['thesaurus_pattern'].replace('thesaurus/',''), '2019-01-01T00:00:00', return_kwargs['lang']
    )
    return_data = get_concept_list(api_path)
    return render_template('thesaurus_new.html', data=return_data, **return_kwargs, subtitle=gettext('Updates'))

@thesaurus_app.route('/about')
#@cache.cached(timeout=None, key_prefix=make_cache_key)
def about():
    get_preferred_language(request, return_kwargs)
    
    return render_template('thesaurus_about.html', **return_kwargs, subtitle=gettext('About'))

@thesaurus_app.route('/search')
def search():
    import unicodedata
    index_name = CONFIG.INDEX_NAME
    query = request.args.get('q', None)
    if not query:
        referrer = request.referrer
        return redirect(referrer)
    preferred_language = request.args.get('lang', 'en')
    if not preferred_language:
        abort(500)
    page = request.args.get('page', '1')

    def remove_control_characters(s):
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    query = remove_control_characters(query)

    #print(ES_CON)

    match = query_es(ES_CON, index_name, query, preferred_language, 8000)
    count = match['hits']['total']
    #print(count)
    response = []
    # Strangely, we can't expect the fields we specify in our query to actually exist.
    for m in match['hits']['hits']:
        try:
            this_r = {
                'score': m['_score'],
                'pref_label': m['_source']['labels_%s' % preferred_language][0],
                'uri': m['_source']['uri'],
                'uf_highlights': []
            }
            try:
                this_h = m['highlight']['alt_labels_%s' % preferred_language]
                this_r['uf_highlights'] = this_h
            except KeyError:
                pass
            response.append(this_r)
        except KeyError:
            pass

    #resp = response[(int(page) - 1) * int(KWARGS['rpp']): (int(page) - 1) * int(KWARGS['rpp']) + int(KWARGS['rpp']) ]
    #pagination = Pagination(page, KWARGS['rpp'], len(response))
    print('Search response:',response)

    #print(pagination.page, page)

    return render_template('thesaurus_search.html', results=resp, query=query, count=count, lang=preferred_language, pagination=pagination, subtitle=gettext('Search'))

@thesaurus_app.route('/autocomplete', methods=['GET'])
def autocomplete():
    index_name = CONFIG.INDEX_NAME
    q = request.args.get('q', None)
    preferred_language = request.args.get('lang', 'en')
    if not q:
        abort(500)
    if not preferred_language:
        abort(500)

    match = query_es(ES_CON, index_name, q, preferred_language, 20)
    results = []
    for res in match['hits']['hits']:
        if not res['_source'].get("labels_%s" % preferred_language):
            continue
        uri = res["_source"]["uri"]
        #print(uri)
        pref_label = res["_source"]["labels_%s" % preferred_language][0]
        
        #print(pref_label)
        results.append({
            'uri': uri,
            'pref_label': pref_label
        })

    return jsonify(results)

@thesaurus_app.route('_expand_category')
@cache.cached(timeout=None, key_prefix=make_cache_key)
def _expand_category():
    '''
    This expands a category and is intended to be used asynchronously by several methods. 
    It returns JSON.
    If it's given no request arguments, it assumes Domain as the type and 01 as the value.
    '''
    category = request.args.get('category', '01')
    category_type = request.args.get('type', 'Domain')
    language = request.args.get('lang','en')
    if category_type in SINGLE_CLASSES:
        this_sc = SINGLE_CLASSES[category_type]
        child_accessor = this_sc['child_accessor_property']
        uri = INIT['uri_base'] + category
        api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
            API['source'], INIT['thesaurus_pattern'], uri, child_accessor, language
        )
        return_data = get_concept(uri, api_path, this_sc, language)

        if category_type == 'Domain':
            return jsonify(return_data['properties']['http://www.w3.org/2004/02/skos/core#hasTopConcept'])
        else:
            return jsonify(return_data['narrowers'])
    else:
        return render_template('404.html', **return_kwargs), 404

