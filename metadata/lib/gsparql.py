'''
This library provides read access to an Ontotext GraphDB endpoint and defines 
some useful methods for retrieving and expanding concepts and relationships.
'''
import json, requests, re
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode

EU = Namespace('http://eurovoc.europa.eu/schema#')
UNBIST = Namespace('http://metadata.un.org/thesaurus/')
SDG = Namespace('http://metadata.un.org/sdg/')
SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

def build_graph(uri, endpoint):
    '''
    Builds a graph from the Concept URI
    '''
    g = Graph()

    g.bind('skos', SKOS)
    g.bind('eu', EU)
    g.bind('dc', DC)
    g.bind('dcterms', DCTERMS)
    g.bind('unbist', UNBIST)
    g.bind('sdg', SDG)
    g.bind('sdgo', SDGO)

    jsonld_context = {
        'skos': SKOS,
        'eu': EU,
        'dc': DC,
        'dcterms': DCTERMS,
        'sdgo': SDGO
    }

    params = {
        'query': f'SELECT ?p ?o {{ <{uri}> ?p ?o }}'
    }
    headers = {
        'Accept': 'application/json'
    }
    response = requests.get(endpoint, headers=headers, params=params)
    json_data = json.loads(response.text)
    if len(json_data['results']['bindings']) == 0:
        return None
    for res in json_data['results']['bindings']:
        s = URIRef(uri)
        p = URIRef(res['p']['value'])
        # default for object is URI, but we'll override if it's a literal
        o = None
        if res['o']['type'] == 'uri':
            o = URIRef(res['o']['value'])
        elif res['o']['type'] == 'literal':
            if 'xml:lang' in res['o']:
                o = Literal(res['o']['value'], lang=res['o']['xml:lang'])
            else:
                o = Literal(res['o']['value'])
        g.add((s,p,o))

    return g

def get_pref_label(uri, g, lang):
    '''
    This returns precisely one of the preferred labels from the concept graph, the English 
    label if none of the other language selections match, or None if there is no label. 
    In case (erroneously) there is more than one prefLabel for the concept, the first 
    encountered is returned.
    '''
    #print(f'Got {lang}')
    try:
        label = [o for o in g.objects(subject=URIRef(uri), predicate=SKOS.prefLabel) if o.language == lang][0]
        #print(f'Found {label} for {lang}')
    except IndexError:
        label = [o for o in g.objects(subject=URIRef(uri), predicate=SKOS.prefLabel) if o.language == 'en'][0]
        #print(f'Found {label} for en')
    except:
        label = None
    return label

def get_lexical_literal(uri, g, predicate, lang):
    #print(predicate)
    '''
    Similar to the above, this returns the first literal value that matches a language 
    for the given predicate. 
    '''
    try:
        literal = [o for s,p,o in g.triples((None, predicate, None)) if o.language == lang][0]
    except IndexError:
        literal = [o for s,p,o in g.triples((None, predicate, None)) if o.language == 'en'][0]
    except:
        literal = None
    return literal

def fetch_external_label(uri, language='en', mimetype='application/rdf+xml'):
    '''
    This function looks at a target URI and attempts to resolve the label.
    It assumes you know what content type you're looking for and that the 
    target service can return objects we can work with...

    You can access the function synchronously or asynchronously as you see fit.
    '''
    # put this in config probably
    whitelisted_sources = [
        {'name':'EuroVoc', 'uri': 'http://eurovoc.europa.eu'},
        {'name':'UNBIS Thesaurus', 'uri': 'http://metadata.un.org/thesaurus'},
        {'name':'SDG', 'uri': 'http://metadata.un.org/sdg'},
        #{'name': 'UN Environment Live', 'uri': 'http://purl.unep.org/sdg/'},
        {'name':'Wikidata', 'uri': 'http://www.wikidata.org'}
    ]

    #print(uri,language,mimetype)

    this_source = next(filter(lambda x: re.match(x['uri'],uri),whitelisted_sources),None)
    #print(this_source)
    if this_source:
        this_doc = requests.get(uri,headers={'accept':mimetype}).text
        g = Graph()
        try:
            g.parse(data=this_doc, format='xml')
        except:
            return_data = {'label': uri, 'uri': uri, 'source': this_source}
            return return_data
        try:
            #this_label = g.preferredLabel(URIRef(uri), lang=language)[0][1]
            this_label = [o for s,p,o in g.triples((None, SKOS.prefLabel, None)) if o.language==language][0]
        except IndexError:
            #this_label = g.preferredLabel(URIRef(uri), lang='en')[0][1]
            this_label = [o for s,p,o in g.triples((None, SKOS.prefLabel, None)) if o.language=='en'][0]
        except IndexError:
            this_label = uri
        return_data = {'label': this_label, 'uri': uri, 'source': this_source}
        #print(return_data)
        return return_data
    else:
        #print("None")
        return None