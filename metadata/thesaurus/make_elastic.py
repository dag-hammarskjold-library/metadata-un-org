import json
from flask import Flask
from elasticsearch import Elasticsearch
from tqdm import tqdm
from config import API, INIT, LANGUAGES, ELASTICSEARCH_URI, INDEX_NAME
import requests, os

elasticsearch_uri = ELASTICSEARCH_URI
index_name = INDEX_NAME
es_con = Elasticsearch(elasticsearch_uri)

thesaurus_index = {
    "settings": {
        "index": {
            "number_of_shards": 3
        },
        "analysis": {
            "analyzer": {
                "autocomplete": {
                    "tokenizer": "autocomplete",
                    "filter": [
                        "lowercase"
                    ]
                },
                "autocomplete_search": {
                    "tokenizer": "lowercase"
                }
            },
            "tokenizer": {
                "autocomplete": {
                    "type": "edge_ngram",
                    "min_gram": 3,
                    "max_gram": 10,
                    "token_chars": [
                        "letter",
                        "digit"
                    ]
                }
            }
        }
    }
}

# Delete index if exists
if es_con.indices.exists(index_name):
    print("deleting '%s' index..." % (index_name))
    res = es_con.indices.delete(index=index_name)
    print(" response: '%s'" % (res))

# Create Index
print("creating {} index...".format(index_name))
res = es_con.indices.create(index=index_name, body=thesaurus_index)
print(" response: {}".format(res))

thesaurus_mapping = {
    "properties": {
        "uri": {"type": "text", "index": "false"},
        "labels_ar": {"type": "text", "analyzer": "arabic"},
        "labels_zh": {"type": "text", "analyzer": "chinese"},
        "labels_en": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
        "labels_fr": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
        "labels_ru": {"type": "text", "analyzer": "russian"},
        "labels_es": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
        "alt_labels_ar": {"type": "text", "analyzer": "arabic"},
        "alt_labels_zh": {"type": "text", "analyzer": "chinese"},
        "alt_labels_en": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
        "alt_labels_fr": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
        "alt_labels_ru": {"type": "text", "analyzer": "russian"},
        "alt_labels_es": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
    }
}

print("creating mapping ...")
res = es_con.indices.put_mapping(index=index_name, doc_type="doc", body=thesaurus_mapping)
print("resonse: {}".format(res))

'''
This part gets an alphabetical/ordered list of terms for each language and writes
them to Elasticsearch
'''
#for lang in LANGUAGES:
print("Getting Data...")

api_path = '%s%s/export?format=RDF/JSON&exportModules=concepts' % (
    API['source'], INIT['project_pattern']
)

#jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
#    if jsresponse.status_code == 200:
#        jsdata = json.loads(jsresponse.text)
this_folder = os.path.dirname(os.path.abspath(__file__))
my_file = os.path.join(this_folder, 'unbst-rdf-json')
jsdata = json.load(open(my_file, 'r'))

for part in ['01','02']:
    cs = 'http://metadata.un.org/thesaurus/{}'.format(part)
    print(cs)

'''    
concept_schemes = get_schemes(api_path)
this_data = []
for cs in concept_schemes:
    subtree_path = '%s%s/subtree?root=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], cs['uri'], lang
    )
    #print(subtree_path)
    concepts = get_concept_list(subtree_path)
    for c in concepts:
        for n in c['narrowers']:
            #print(n['concept']['uri'])
            all_uris.append(n['concept']['uri'])

#documents = []
print("Getting data and building ES index...")
for uri in tqdm(all_uris):
    doc = {"uri": uri}
    for lang in LANGUAGES:
        properties = 'skos:prefLabel,skos:altLabel'
        api_path = '%s%s/concept?concept=%s&language=%s&properties=%s' % (
            API['source'], INIT['thesaurus_pattern'], uri, lang, properties
        )
        #print(api_path)
        jsresponse = requests.get(api_path, auth=(API['user'],API['password']))
        if jsresponse.status_code == 200:
            jsdata = json.loads(jsresponse.text)
            #print(jsdata)
            doc.update({'labels_{}'.format(lang): jsdata['prefLabel']})

            try:
                alt_labels = []
                for label in jsdata['altLabels']:
                    alt_labels.append(label)
                doc.update({'alt_labels_{}'.format(lang): alt_labels})
            except KeyError:
                pass

            # Let's load it up
            payload = json.dumps(doc)
            res = es_con.index(index=index_name, doc_type='doc', body=payload)

    #documents.append(doc)
'''