from flask import render_template, redirect, url_for, request, jsonify, abort, json
from metadata import cache
from metadata.config import API
from metadata.semantic import Term
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import INIT, SINGLE_CLASSES, LANGUAGES, KWARGS
from metadata.config import GLOBAL_KWARGS, GRAPH
from metadata.utils import get_preferred_language
import re, requests

# Common set of kwargs to return in all cases. 
return_kwargs = {
    **KWARGS,
    **GLOBAL_KWARGS
}

def make_cache_key(*args, **kwargs):
    '''
    Quick function to make cache keys with the full
    path of the request, including search strings
    '''
    path = request.full_path
    return path

@thesaurus_app.route('/')
#@cache.cached(timeout=None, key_prefix=make_cache_key)
def index():
    '''
    This should return a landing page for the thesaurus application. 
    The landing page should provide a description for the resource  
    and links to its child objects.
    '''
    get_preferred_language(request, return_kwargs)
    out_format=request.args.get('format','html')
    this_sc = SINGLE_CLASSES['Root']
    uri = this_sc['uri']
    return_properties = ",".join(this_sc['properties'])
    api_path = '%s%s/concept?concept=%s&properties=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], uri, return_properties, return_kwargs['lang']
    )
    #print(api_path)
    jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
    if jsresponse.status_code == 200:
        jsdata = json.loads(jsresponse.text)

        # Get preferred labels
        jsdata['labels'] = get_labels(uri, 'skos:prefLabel', LANGUAGES)

        # Make JSON output
        if out_format == 'json':
            return jsonify(jsdata)

        # Relationships, sorted by label
        child_accessor = this_sc['child_accessor_property']
        jsdata['parts'] = build_list(jsdata['properties'][child_accessor], 'prefLabel')

    
        return render_template('thesaurus_index.html', **return_kwargs, data=jsdata)
    else:
        abort(404)

@thesaurus_app.route('/<id>')
#@cache.cached(timeout=None, key_prefix=make_cache_key)
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
    if id == '00':
        return redirect('/')
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

                # Get breadcrumbs
                breadcrumbs = build_breadcrumbs(uri)

                # Get relationships with labels, sorted
                for lst in this_sc['lists']:
                    #print(lst)
                    try:
                        jsdata[lst] = build_list(jsdata[lst],'prefLabel')
                    except KeyError:
                        try:
                            child_accessor = this_sc['child_accessor_property']
                            jsdata[lst] = build_list(jsdata['properties'][child_accessor], 'prefLabel')
                        except KeyError:
                            pass
                this_title = KWARGS['title']
                return render_template(this_sc['template'], **return_kwargs, data=jsdata, bcdata=breadcrumbs)
            else:
                abort(404)
        else:
            next
    abort(404)

@thesaurus_app.route('/search')
def search():
    return render_template('search.html', **return_kwargs)

def build_breadcrumbs(uri):
    api_path = '%s%s/paths?concept=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], uri, return_kwargs['lang']
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
            print(bc)
        return bcdata
    else:
        return None

def build_list(concepts, sort_key):
    '''
    This takes a list of URIs and returns a list of uri,label tuples sorted by the label
    in the selected language.
    '''
    #print(concepts)
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
