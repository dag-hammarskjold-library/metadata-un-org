from flask import render_template, redirect, url_for, request, jsonify, abort, json
from metadata import cache
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language
import re, requests

# Common set of kwargs to return, just in case
#return_kwargs = {
#    **KWARGS,
#    **GLOBAL_KWARGS
#}

API = CONFIG.API
INIT = CONFIG.INIT
SINGLE_CLASSES = CONFIG.SINGLE_CLASSES
LANGUAGES = CONFIG.LANGUAGES
KWARGS = CONFIG.KWARGS
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS

def make_cache_key(*args, **kwargs):
    '''
    Quick function to make cache keys with the full
    path of the request, including search strings
    '''
    path = request.full_path
    return path

def get_concept(uri, api_path, this_sc, lang):
    '''
    This function takes a full API path and returns formatted data for display in the templates.
    '''
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        jsdata = json.loads(jsresponse.text)

        # Get preferred labels
        jsdata['labels'] = get_labels(uri=uri, label_type='skos:prefLabel', langs=LANGUAGES)

        # Get dc:identifiers, if any
        #print(jsdata)
        try:
            jsdata['identifier'] = jsdata['properties']['http://purl.org/dc/elements/1.1/identifier'][0]
        except KeyError:
            pass

        # Get breadcrumbs
        breadcrumbs = build_breadcrumbs(uri, lang)
        jsdata['bcdata'] = breadcrumbs

        #print(this_sc)

        for r in this_sc['display_properties']:
            #print(r)
            try:
                this_list = jsdata[r]
                #print(this_list)
                jsdata[r] = build_list(this_list, this_sc['child_sort_key'], lang)
            except KeyError:
                try:
                    this_list = jsdata['properties'][r]
                    jsdata['properties'][r] = build_list(this_list, this_sc['child_sort_key'], lang)
                except KeyError:
                    pass

        jsdata['pageTitle'] = "%s| %s" % (jsdata['prefLabel'],KWARGS['title'])
        #print(jsdata)
        return jsdata
    else:
        return None

@cache.memoize(timeout=None)
def get_schemes(api_path):
    '''
    This function gets a list of the concept schemes available in the resource.
    '''
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        jsdata = json.loads(jsresponse.text)
        for jsd in jsdata:
            #this_sc = SINGLE_CLASSES['']
            d_identifier = jsd['uri'].split('/')[-1]
            jsd['identifier'] = d_identifier
            
            # Get the top concepts of each scheme
            #jsdata['childconcepts'] = build_list()
        return_data = sorted(jsdata, key=lambda k: k['uri'])
    else:
        return None

    return return_data

@cache.memoize(timeout=None)
def get_concept_list(api_path):
    '''
    This function gets a list of the concept schemes available in the resource.
    '''
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        jsdata = json.loads(jsresponse.text)
        #return_data = sorted(jsdata, key=lambda k: k['uri'])
        return jsdata
    else:
        return None

def get_labels(uri, label_type, langs):
    labels = []
    for lang in langs:
        api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
            API['source'], INIT['thesaurus_pattern'], uri, label_type, lang
        )
        jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
        if jsresponse.status_code == 200:
            jsdata = json.loads(jsresponse.text)
            accessor = label_type.split(':')[1]
            try:
                label = jsdata[accessor]
                labels.append({'lang': lang, 'label': jsdata[accessor]})
            except KeyError:
                pass
    return labels

def build_breadcrumbs(uri, lang):
    api_path = '%s%s/paths?concept=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], uri, lang
    )
    #print(api_path)
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        bcdata = json.loads(jsresponse.text)
        for bc in bcdata:
            d_identifier = bc['conceptScheme']['uri'].split('/')[-1]
            bc['conceptScheme']['identifier'] = d_identifier
            mt_identifier = bc['conceptPath'][0]['uri'].split('/')[-1]
            bc['conceptPath'][0]['identifier'] = '.'.join(re.findall(r'.{1,2}', mt_identifier))
            #print(bc)
        return bcdata
    else:
        return None

def build_list(concepts, sort_key, lang):
    '''
    This takes a list of URIs and returns a list of uri,label tuples sorted by the label
    in the selected language.
    '''
    #print(concepts)
    #api_path = '%s%s/concepts?concepts=%s&language=%s&properties=dc:identifier' %(
    #    API['source'], INIT['thesaurus_pattern'], ",".join(concepts), lang
    #)
    #print(api_path)
    api_path = '%s%s/concepts' %( API['source'], INIT['thesaurus_pattern'] )
    api_data = {'concepts': ",".join(concepts), 'language': lang, 'properties': 'dc:identifier'}
    jsresponse = requests.post(api_path, data=api_data, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        jsdata = json.loads(jsresponse.text)
        sort_data = []
        for jsd in jsdata:
            try:
               jsd['dc:identifier'] = jsd['properties']['http://purl.org/dc/elements/1.1/identifier'][0]
            except KeyError:
                pass
            sort_data.append(jsd)
        #print(jsdata)
        sorted_js = sorted(jsdata, key=lambda k: k[sort_key])
        return sorted_js
    else:        
        return None

# Pagination class, source: http://flask.pocoo.org/snippets/44/
class Pagination(object):
    
    def __init__(self, page, rpp, count):
        self.page = page
        self.rpp = rpp
        self.count = count

    @property
    def pages(self):
        return int(ceil(self.count / float(self.rpp)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last=0
        for num in xrange(1, self.pages +1):
            if num <= left_edge or (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                if last +1 != num:
                    yield None
                yield num
                last = num
