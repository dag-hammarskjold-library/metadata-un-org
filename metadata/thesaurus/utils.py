from flask import render_template, redirect, url_for, request, jsonify, abort, json
from metadata import cache
from metadata.config import API
from metadata.semantic import Term
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import INIT, SINGLE_CLASSES, LANGUAGES, KWARGS
from metadata.config import GLOBAL_KWARGS, GRAPH
from metadata.utils import get_preferred_language
import re, requests

# Common set of kwargs to return, just in case
#return_kwargs = {
#    **KWARGS,
#    **GLOBAL_KWARGS
#}

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

        for r in this_sc['display_properties']:
            try:
                this_list = jsdata[r]
                jsdata[r] = build_list(this_list, this_sc['child_sort_key'], lang)
            except KeyError:
                try:
                    this_list = jsdata['properties'][r]
                    jsdata['properties'][r] = build_list(this_list, this_sc['child_sort_key'], lang)
                except KeyError:
                    pass

        jsdata['pageTitle'] = "%s| %s" % (jsdata['prefLabel'],KWARGS['title'])
        print(jsdata)
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
    api_path = '%s%s/concepts?concepts=%s&language=%s&properties=dc:identifier' %(
        API['source'], INIT['thesaurus_pattern'], ",".join(concepts), lang
    )
    print(api_path)
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
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