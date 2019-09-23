from docopt import docopt
from tqdm import tqdm
from config import API, INIT, KWARGS, LANGUAGES
import importlib, json, requests, re

return_kwargs = KWARGS

return_kwargs['lang'] = 'zh'


api_path = '%s%s/schemes?language=%s' % (
    API['source'], INIT['thesaurus_pattern'], return_kwargs['lang']
)

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
            print(r)
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

concept_schemes = get_schemes(api_path)
this_data = {}
labels = []

print("Getting concept in each concept scheme.")
for cs in concept_schemes:
    print("Processing %s" % cs['uri'])
    subtree_path = '%s%s/subtree?root=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], cs['uri'], return_kwargs['lang']
    )
    concepts = get_concept_list(subtree_path)
    for c in concepts:
        for n in c['narrowers']:
            try:
                concept = n['concept']
                #print(concept)
                this_label = concept['prefLabel']
                if this_label not in labels:
                    labels.append(this_label)
                if this_label not in this_data:
                    this_data[this_label] = [concept['uri']]
                else:
                    this_data[this_label].append(concept['uri'])
            except TypeError:
                pass

# The following comes from https://github.com/cipang/chinese-sort

from sortdata import data
keyed_labels = []

for s in labels:
    l = list()
    for c in s:
        code = ord(c)
        if c.isupper() or c.islower() or c.isspace() or c.isdigit():
            l.append(0)   # Strokes.
            l.append(code)   # Frequency.
        else:
            if code in data:
                l.append(data[code]["kTotalStrokes"])
                l.append(data[code]["kFrequency"])
                l.append(code)
            else:
                l.append(99)
                l.append(99)
                l.append(code)
    this_key = (tuple(l))
    keyed_labels.append({'label':s,'key':this_key})

sorted_labels = sorted(keyed_labels, key=lambda k: k['key'])

output_data = []
for sl in sorted_labels:
    for uri in this_data[sl['label']]:
        output = '<div class="row"><a class="bc-link" href="%s?lang=zh">%s</a></div>\n' % (uri, sl['label'])
        if output not in output_data:
            output_data.append(output)

print("Writing output.")
# <a class="bc-link" href="URI?lang=zh">LABEL</a>
with open('_chinese_sorted.html', 'w+') as f:
    for o in output_data:
        f.write(o)
        