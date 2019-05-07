alphabetic_index = {
    "settings": {
        "index": {
            "number_of_shards": 3
        },
        "analysis": {
            "analyzer"
        }
    }
}


'''
This part gets an alphabetical/ordered list of terms for each language and writes
them to Elasticsearch
'''
api_path = '%s%s/schemes?language=%s' % (
    API['source'], INIT['thesaurus_pattern'], return_kwargs['lang']
)
    
concept_schemes = get_schemes(api_path)
this_data = []
for cs in concept_schemes:
    tc_path = '%s%s/topconcepts?scheme=%s&language=%s' % (
        API['source'], INIT['thesaurus_pattern'], cs['uri'], return_kwargs['lang']
    )
    microthesauri = get_schemes(tc_path)
    for mt in microthesauri:
        subtree_path = tc_path = '%s%s/subtree?root=%s&language=%s' % (
            API['source'], INIT['thesaurus_pattern'], mt['uri'], return_kwargs['lang']
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