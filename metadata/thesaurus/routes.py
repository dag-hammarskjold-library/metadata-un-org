from flask import render_template, redirect, url_for, request, jsonify, abort, json
from metadata.config import API
from metadata.semantic import Term
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import INIT, LIST_CLASSES, SINGLE_CLASSES, LANGUAGES, KWARGS
from metadata.config import GLOBAL_KWARGS, GRAPH
from metadata.utils import get_preferred_language
import re, requests

# Common set of kwargs to return in all cases. 
return_kwargs = {
    **KWARGS,
    **GLOBAL_KWARGS
}

@thesaurus_app.route('/')
def index():
    '''
    This should return a landing page for the thesaurus application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    get_preferred_language(request, return_kwargs)
    return render_template('thesaurus_index.html', **return_kwargs)

@thesaurus_app.route('/<id>')
def get_by_id(id):
    '''
    This should return the landing page for a single instance of
    a record, such as an individual Concept.

    Positive matching is done against a whitelist of RDF Types 
    and id regular expressions patterns as definied in 
    metadata.thesaurus.config. This is intended to pre-screen 
    user input and reject anything that doesn't fit a strict 
    pattern.
    '''
    get_preferred_language(request, return_kwargs)
    out_format=request.args.get('format','html')
    for single_class in SINGLE_CLASSES:
        this_sc = SINGLE_CLASSES[single_class]
        p = re.compile(this_sc['id_regex'])
        if p.match(id):
            #print(this_sc)
            uri = INIT['uri_base'] + id
            return_properties = ",".join(this_sc['properties'])
            api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
                API['source'], INIT['thesaurus_pattern'], uri, return_properties, return_kwargs['lang']
            )
            #print(api_path)
            breadcrumbs = build_breadcrumbs(uri)
            jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
            if jsresponse.status_code == 200:
                jsdata = json.loads(jsresponse.text)

                # Get rdf:types
                jsdata['types'] = []
                for t in jsdata['properties']['http://www.w3.org/1999/02/22-rdf-syntax-ns#type']:
                    jsdata['types'].append(t.split('#')[1])

                # Get preferred labels
                jsdata['labels'] = get_labels(uri, 'skos:prefLabel', LANGUAGES)

                # We can return bare json now if we like:
                if out_format == 'json':
                    return jsonify(jsdata)

                # Get relationships with labels, sorted
                for lst in this_sc['lists']:
                    print(lst)
                    try:
                        jsdata[lst] = build_list(jsdata[lst],'prefLabel')
                    except KeyError:
                        try:
                            child_accessor = this_sc['child_accessor_property']
                            jsdata[lst] = build_list(jsdata['properties'][child_accessor], 'prefLabel')
                        except KeyError:
                            pass
                
                return render_template(this_sc['template'], **return_kwargs, data=jsdata, bcdata=breadcrumbs)
            else:
                abort(404)
        else:
            next
    abort(404)

@thesaurus_app.route('/browse/<list_class>')
def browse(list_class):
    '''
    This should return the landing page for a listable class of 
    records, such as ConceptSchemes, Domains, etc.
    '''
    get_preferred_language(request, return_kwargs)

    if list_class in LIST_CLASSES:
        this_lc = LIST_CLASSES[list_class]
        return render_template(this_lc['template'], **return_kwargs)
    else:
        abort(403)

@thesaurus_app.route('/search')
def search():
    return render_template('search.html', **return_kwargs)

def build_breadcrumbs(uri):
    api_path = '%s%s/paths?concept=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], uri, return_kwargs['lang']
    )
    print(api_path)
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        bcdata = json.loads(jsresponse.text)
        return bcdata
    else:
        return None

def build_list(concepts, sort_key):
    '''
    This takes a list of URIs and returns a list of uri,label tuples sorted by the label
    in the selected language.
    '''
    print(concepts)
    api_path = '%s%s/concepts?concepts=%s&language=%s' %(
        API['source'], INIT['thesaurus_pattern'], ",".join(concepts), return_kwargs['lang']
    )
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        jsdata = json.loads(jsresponse.text)
        sorted_js = sorted(jsdata, key=lambda k: k[sort_key])
        return sorted_js
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