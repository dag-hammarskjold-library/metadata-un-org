from metadata.thesaurus import thesaurus_app
from metadata.lib.ppmdb import *
from metadata.thesaurus.config import CONFIG
import click, os

@thesaurus_app.cli.command('reload-concept')
@click.argument('uri')
def re_load_concept(uri):
    languages = CONFIG.LANGUAGES
    reload_concept(uri, languages)


@thesaurus_app.cli.command('reindex-concept')
@click.argument('uri')
def reindex_concept(uri):
    pass

@thesaurus_app.cli.command('rebuild-index')
#@click.argument('command')
@click.argument('datafile')
def rebuild_index(datafile):
    from elasticsearch import Elasticsearch
    from rdflib import plugin, ConjunctiveGraph, Namespace, Literal, URIRef
    from rdflib.namespace import SKOS 
    from tqdm import tqdm
    import importlib, json, requests
    import ssl
    from elasticsearch.connection import create_ssl_context

    context = create_ssl_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    es_uri = CONFIG.ELASTICSEARCH_URI
    es_con = Elasticsearch(es_uri, ssl_context=context)
    index_name = CONFIG.INDEX_NAME

    if not os.path.exists(datafile):
        raise "file not found"

    print(f"Deleting {index_name}")
    if es_con.indices.exists(index_name):
        res = es_con.indices.delete(index_name)

    print(f"Creating {index_name}")
    body = CONFIG.THESAURUS_INDEX
    res = es_con.indices.create(index_name, body=body)

    print(f"Preparing mapping")
    mapping = CONFIG.MAPPING
    res = es_con.indices.put_mapping(index=index_name, body=mapping)

    print(f"Building index from {datafile}")
    graph = ConjunctiveGraph()
        
    try:
        graph.parse(datafile, format='ttl')
    except:
        raise

    #querystring = """PREFIX eu: <http://eurovoc.europa.eu/schema#> select ?uri where { ?uri rdf:type skos:Concept . MINUS { ?uri rdf:type eu:MicroThesaurus . } }"""
    querystring = querystring = """
PREFIX eu: <http://eurovoc.europa.eu/schema#> 
PREFIX dcterms: <http://purl.org/dc/terms/> 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT * WHERE {
    {
		select ?uri ?tcode where { 
    		?uri rdf:type skos:Concept . 
    		MINUS { 
        		?uri rdf:type eu:MicroThesaurus . 
    		} . 
    		?uri dcterms:identifier ?tcode .  
			FILTER( strStarts( ?tcode, 'T')) .
        } 
    } UNION {
		select ?uri ?tcode where {
			?uri rdf:type skos:Concept .
			MINUS {
				?uri rdf:type eu:MicroThesaurus .
			} .
			FILTER NOT EXISTS { ?uri dcterms:identifier ?tcode }
		}
	}
}"""

    for uri, tcode in tqdm(graph.query(querystring)):
    #for uri, tcode in graph.query(querystring):
        this_uri = uri
        this_tcode = tcode
        #print(this_uri, this_tcode)
        doc = {"uri": this_uri}
        for lang in CONFIG.LANGUAGES:
            pref_labels = []
            for label in graph.preferredLabel(URIRef(this_uri), lang):
                pref_labels.append(label[1])
            doc.update({"labels_{}".format(lang): pref_labels})

            alt_labels = []
            for label in graph.objects(URIRef(this_uri), SKOS.altLabel):
                if label.language == lang:
                    alt_labels.append(label)
            doc.update({"alt_labels_{}".format(lang): alt_labels})
            if tcode is not None:
                doc.update({"tcode": this_tcode}) 

            payload = json.dumps(doc)
            print(payload)

            res = es_con.index(index=index_name, body=payload)
            doc = {"uri": this_uri}