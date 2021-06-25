from metadata.thesaurus.utils import mint_tcode
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

    #for uri, tcode in tqdm(graph.query(querystring)):
    for uri, tcode in graph.query(querystring):
        this_uri = uri
        this_tcode = tcode
        print(this_uri, this_tcode)
        doc = {"uri": this_uri}
        for lang in CONFIG.LANGUAGES:
            pref_labels = []
            for label in graph.preferredLabel(URIRef(this_uri), lang):
                #print(label)
                pref_labels.append(label[1])
            doc.update({"labels_{}".format(lang): pref_labels})

            alt_labels = []
            for label in graph.objects(URIRef(this_uri), SKOS.altLabel):
                if label.language == lang:
                    alt_labels.append(label)
            doc.update({"alt_labels_{}".format(lang): alt_labels})

            if tcode is not None:
                doc.update({"tcode": this_tcode}) 

            hidden_labels = []
            for label in graph.objects(URIRef(this_uri), SKOS.hiddenLabel):
                if label.language == lang:
                    hidden_labels.append(label)
            doc.update({"hidden_labels_{}".format(lang): hidden_labels})

            payload = json.dumps(doc)
            print(payload)

            res = es_con.index(index=index_name, body=payload)
            doc = {"uri": this_uri}

@thesaurus_app.cli.command('upsert-marc')
@click.argument('uri')
@click.option('--auth-control/--no-auth-control', default=True)
def upsert_marc(uri, auth_control):
    from dlx.marc import DB, Auth, Query, Condition, Datafield
    from metadata.thesaurus.utils import to_marc, merged, mint_tcode, save_tcode
    import re

    DB.connect(CONFIG.dlx_connect)

    print(f"Auth control {auth_control}")

    a = Auth.from_query(Query(Condition('035', {'a': uri})))
    try:
        # already exists, so we can update
        this_id = a.id
        skos_marc = to_marc(uri, auth_control)

        marc_auth = Auth.from_id(int(this_id))

        merged_marc = merged(marc_auth, skos_marc)

        this_tcode = None
        make_tcode = False

        for identifier in merged_marc.get_values('035','a'):
            if re.match("^T.*", identifier):
                this_tcode = identifier
        if this_tcode is None:
            this_tcode = mint_tcode()
            field = Datafield(tag='035', record_type='auth').set('a', this_tcode)
            merged_marc.fields.append(field)
            make_tcode = True

        # Step 6: Save the record to the database.
        merged_marc.commit()

        # Step 7: Save the tcode to the thesaurus_codes collection
        if make_tcode:
            save_tcode(this_tcode, this_id, merged_marc.get_value('150','a'), uri)

    except AttributeError:
        # doesn't already exist, so we can create
        try:
            skos_marc = to_marc(uri, auth_control)
        except:
            raise

        new_tcode = mint_tcode()

        skos_marc.set('035','a', new_tcode, address=["+"])

         # Step 4: Set the 008
        skos_marc.set_008()

        # Step 5: Commit the new record. 
        if not auth_control:
            print("Creating this term for linking to other terms. Re-run this command after the terms that depend on it are created.")

        skos_marc.commit()
        
        # Step 6: Get the id of the newly committed record
        query = Query({})
        marc_auth = Auth.from_query(Query(Condition('035', {'a': new_tcode})))
        
        # Step 7: save the tcode to the thesaurus_codes collection
        save_tcode(new_tcode, str(marc_auth.id), skos_marc.get_value('150','a'), uri)
    except:
        raise

@thesaurus_app.cli.command('make-marc')
@click.argument('uri')
@click.option('--auth-control/--no-auth-control', default=True)
def make_marc(uri, auth_control):
    #from dlx.marc import DB, Auth, Query, Condition, Datafield
    from metadata.thesaurus.utils import to_mrc
    import re


    # doesn't already exist, so we can create
    try:
        skos_marc = to_mrc(uri)
    except:
        raise

        # Step 4: Set the 008
    #skos_marc.set_008()

    print(skos_marc)