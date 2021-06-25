from flask import render_template, redirect, url_for, request, jsonify, abort, json
from mongoengine import connect
from elasticsearch import Elasticsearch
from metadata import cache
from metadata.thesaurus import thesaurus_app
from metadata.thesaurus.config import CONFIG
from metadata.config import GLOBAL_CONFIG
from metadata.utils import get_preferred_language
from metadata.lib.ppmdb import Concept, Label, Relationship, reload_concept
from metadata.lib.poolparty import PoolParty, Thesaurus
import re, requests, ssl


from pymongo import MongoClient
from dlx import DB
from dlx.marc import Bib, Auth, Datafield, DB as DLX

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import SKOS 

EU = Namespace('http://eurovoc.europa.eu/schema#')
DC = Namespace('http://purl.org/dc/elements/1.1/')
DCTERMS = Namespace("http://purl.org/dc/terms/")
UNBIST = Namespace('http://metadata.un.org/thesaurus/')
SDG = Namespace('http://metadata.un.org/sdg/')
SDGO = Namespace('http://metadata.un.org/sdg/ontology#')

dlx_db = MongoClient(CONFIG.dlx_connect)['undlFiles']

# Common set of kwargs to return, just in case
#return_kwargs = {
#    **KWARGS,
#    **GLOBAL_KWARGS
#}


INIT = CONFIG.INIT
#SINGLE_CLASSES = CONFIG.SINGLE_CLASSES
LANGUAGES = CONFIG.LANGUAGES
KWARGS = CONFIG.KWARGS
GLOBAL_KWARGS = GLOBAL_CONFIG.GLOBAL_KWARGS

connect(host=CONFIG.connect_string, db=CONFIG.db_name, ssl_cert_reqs=ssl.CERT_NONE)
pool_party = PoolParty(CONFIG.endpoint, CONFIG.project_id, CONFIG.username, CONFIG.password)
thesaurus = Thesaurus(pool_party)

def get_or_update(uri, languages=['en']):
    '''
    First try getting from the database. If that fails, reload from PoolParty
    '''
    print(uri)
    try:
        concept = Concept.objects.get(uri=uri)
        return concept
    except:
        reload_true = reload_concept(uri, languages)
        if reload_true:
            concept = Concept.objects.get(uri=uri)
            return concept
        else:
            return None

def replace_concept(uri):
    print(uri)
    try:
        reload_concept(uri, thesaurus)
        return True
    except:
        return False

def reindex_concept(concept):
    es_con = Elasticsearch(CONFIG.ELASTICSEARCH_URI)
    index_name = CONFIG.INDEX_NAME
    doc = {"uri": concept.uri}
    identifiers = concept.get_property_values_by_predicate('http://purl.org/dc/elements/1.1/identifier')
    tcode = next(filter(lambda x: re.match(r'^T',x['label']), identifiers),None)
    for lang in CONFIG.LANGUAGES:
        pref_labels = []
        for label in concept.get_labels('pref_labels',lang):
            pref_labels.append(label.label)
        doc.update({"labels_{}".format(lang): pref_labels})

        alt_labels = []
        for label in concept.get_labels('alt_labels',lang):
            alt_labels.append(label.label)
        doc.update({"alt_labels_{}".format(lang): alt_labels})

        if tcode is not None:
            doc.update({"tcode": tcode}) 
        

        payload = json.dumps(doc)

        print(doc)

        res = es_con.index(index=index_name, doc_type='_doc', body=payload)
        doc = {"uri": concept.uri}

    return True

# TCode tools
def mint_tcode():
    
    res = dlx_db.thesaurus_codes.find().sort("field_035", -1).limit(1)
    max_code = res[0]['field_035']
    str_code = max_code.replace("T","")
    int_code = int(str_code)
    new_int_code = int_code + 1
    new_code = "T" + str(new_int_code).rjust(7,"0")

    return new_code

def save_tcode(tcode, auth_id, label, uri):
    try:
        #print(tcode, auth_id, label, uri)
        dlx_db.thesaurus_codes.insert_one({
            "field_035": tcode,
            "field_001": auth_id,
            "field_150": label,
            "uri": uri
        })
    except:
        raise

def get_all():
    results = dlx_db.thesaurus_codes.find().sort("uri")
    return_results = []
    for res in results:
        try:
            this_r = {
                'field_035': res["field_035"],
                'field_001': res["field_001"],
                'field_150': res["field_150"],
                'uri': res["uri"]
            }
            if this_r not in return_results:
                return_results.append(this_r)
        except KeyError:
            next
    return return_results


# SKOS to MARC tools, some of which are at least partially duplicated
def populate_graph(graph=None, uri=None):

    if graph is None:
        graph = Graph()
    g = Graph()
    g.bind('skos', SKOS)
    g.bind('eu', EU)
    g.bind('dc', DC)
    g.bind('dcterms', DCTERMS)
    g.bind('unbist', UNBIST)
    g.bind('sdg', SDG)
    g.bind('sdgo', SDGO)

    headers = {'accept': 'text/turtle'}
    ttl = requests.get(uri, headers=headers).text

    try:
        graph.parse(data=ttl, format="turtle")
        for triple in graph:
            g.add(triple)
    except:
        raise

    return g

def to_marc(uri, auth_control=True):

    DLX.connect(CONFIG.dlx_connect)

    lang_tags_map = CONFIG.lang_tags_map

    g = populate_graph(graph=None, uri=uri)

    auth = Auth()
    #auth.set("035", "a", uri)
    field = Datafield(tag='035', record_type='auth').set('a', uri)
    auth.fields.append(field)
    
    for f035 in g.objects(URIRef(uri), DCTERMS.identifier):
        if "lib-thesaurus" in f035:
            pass
        else:
            #auth.set('035', 'a', f035, address=["+"])
            field = Datafield(tag='035', record_type='auth').set('a', f035)
            auth.fields.append(field)

    auth.set_values(
        ('040','a', 'NNUN'),
        ('040','b', 'eng'),
        ('040','f', 'unbist')
    )

    # Process this if we get the signal, otherwise skip it.
    if auth_control:
        # Two types of broader terms: one forms the dot-notated hierarchy, e.g., 01.01.00
        # The other forms broader terms in the usual sense (i.e, to other proper terms)
        for f072a in g.objects(URIRef(uri), SKOS.broader):
            bc = f072a.split('/')[-1]
            if len(bc) == 6:
                n = 2
                chunks = [bc[i:i+n] for i in range(0, len(bc), n)]
                dotted = ".".join(chunks)
                field = Datafield(tag='072', record_type='auth')
                field.ind1 = '7'
                field.ind2 = ' '
                field.set('a', dotted)
                field.set('2', 'unbist')
                auth.fields.append(field)
            else:
                populate_graph(graph=g, uri=f072a)
                for f550 in g.objects(URIRef(f072a), SKOS.prefLabel):
                    if f550.language == 'en':
                        try:
                            #auth.set('550', 'w', 'g', {'address': ["+"]})
                            #auth.set('550','a', f550)
                            datafield = Datafield(tag="550", record_type="auth").set('w', 'g').set('a', f550, auth_control=True)
                            auth.fields.append(datafield)
                        except:
                            print(f"Could not assign {f550} to 550 as a broader term")
                            pass

    
        # related terms go in 550 with only $a
        for f550 in g.objects(URIRef(uri), SKOS.related):
            populate_graph(graph=g, uri=f550)
            for preflabel in g.objects(URIRef(f550), SKOS.prefLabel):
                if preflabel.language == 'en':
                        try:
                            #auth.set('550', 'w', 'g', address=["+"])
                            #auth.set('550','a', preflabel, address=["+"])
                            datafield = Datafield(tag="550", record_type="auth").set('a', preflabel, auth_control=True)
                            auth.fields.append(datafield)
                            
                        except:
                            print(f"Could not assign {preflabel} to 550 as a related term")
                            raise
                            pass


        # narrower terms go in 550 with $w = h
        for f550 in g.objects(URIRef(uri), SKOS.narrower):
            populate_graph(graph=g, uri=f550)
            for preflabel in g.objects(URIRef(f550), SKOS.prefLabel):
                if preflabel.language == 'en':
                        try:
                            #auth.set('550', 'w', 'h', {'address': ["+"]})
                            #auth.set('550','a', preflabel)
                            datafield = Datafield(tag="550", record_type="auth").set('w', 'h').set('a', preflabel, auth_control=True)
                            auth.fields.append(datafield)
                        except:
                            print(f"Could not assign {preflabel} to 550 as a narrower term")
                            pass
        
    # English pref labels go in 150
    for f150 in g.objects(URIRef(uri), SKOS.prefLabel):
        field = Datafield(tag=lang_tags_map[f150.language]['prefLabel'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f150)
        auth.fields.append(field)

    # English alt labels go in 450
    for f450 in g.objects(URIRef(uri), SKOS.altLabel):
        field = Datafield(tag=lang_tags_map[f450.language]['altLabel'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f450)
        auth.fields.append(field)

    # English scope notes go in 680
    for f680 in g.objects(URIRef(uri), SKOS.scopeNote):
        field = Datafield(tag=lang_tags_map[f680.language]['scopeNote'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f680)
        auth.fields.append(field)

    # 688? 

    # English general/source notes go in 670, other langs in 933-937
    for f670 in g.objects(URIRef(uri), SKOS.note):
        field = Datafield(tag=lang_tags_map[f670.language]['note'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f670)
        auth.fields.append(field)
    
    return auth

def to_mrc(uri):
    #DLX.connect(CONFIG.dlx_connect)

    lang_tags_map = CONFIG.lang_tags_map

    g = populate_graph(graph=None, uri=uri)

    auth = Auth()
    #auth.set("035", "a", uri)
    field = Datafield(tag='035', record_type='auth').set('a', uri)
    auth.fields.append(field)
    
    for f035 in g.objects(URIRef(uri), DCTERMS.identifier):
        if "lib-thesaurus" in f035:
            pass
        else:
            #auth.set('035', 'a', f035, address=["+"])
            field = Datafield(tag='035', record_type='auth').set('a', f035)
            auth.fields.append(field)

    auth.set_values(
        ('040','a', 'NNUN'),
        ('040','b', 'eng'),
        ('040','f', 'unbist')
    )

    # Two types of broader terms: one forms the dot-notated hierarchy, e.g., 01.01.00
    # The other forms broader terms in the usual sense (i.e, to other proper terms)
    for f072a in g.objects(URIRef(uri), SKOS.broader):
        bc = f072a.split('/')[-1]
        if len(bc) == 6:
            n = 2
            chunks = [bc[i:i+n] for i in range(0, len(bc), n)]
            dotted = ".".join(chunks)
            field = Datafield(tag='072', record_type='auth')
            field.ind1 = '7'
            field.ind2 = ' '
            field.set('a', dotted)
            field.set('2', 'unbist')
            auth.fields.append(field)
        else:
            populate_graph(graph=g, uri=f072a)
            for f550 in g.objects(URIRef(f072a), SKOS.prefLabel):
                if f550.language == 'en':
                    try:
                        #auth.set('550', 'w', 'g', {'address': ["+"]})
                        #auth.set('550','a', f550)
                        datafield = Datafield(tag="550", record_type="auth").set('w', 'g').set('a', f550, auth_control=False)
                        auth.fields.append(datafield)
                    except:
                        print(f"Could not assign {f550} to 550 as a broader term")
                        pass


    # related terms go in 550 with only $a
    for f550 in g.objects(URIRef(uri), SKOS.related):
        populate_graph(graph=g, uri=f550)
        for preflabel in g.objects(URIRef(f550), SKOS.prefLabel):
            if preflabel.language == 'en':
                    try:
                        #auth.set('550', 'w', 'g', address=["+"])
                        #auth.set('550','a', preflabel, address=["+"])
                        datafield = Datafield(tag="550", record_type="auth").set('a', preflabel, auth_control=False)
                        auth.fields.append(datafield)
                        
                    except:
                        print(f"Could not assign {preflabel} to 550 as a related term")
                        raise
                        pass


    # narrower terms go in 550 with $w = h
    for f550 in g.objects(URIRef(uri), SKOS.narrower):
        populate_graph(graph=g, uri=f550)
        for preflabel in g.objects(URIRef(f550), SKOS.prefLabel):
            if preflabel.language == 'en':
                    try:
                        #auth.set('550', 'w', 'h', {'address': ["+"]})
                        #auth.set('550','a', preflabel)
                        datafield = Datafield(tag="550", record_type="auth").set('w', 'h').set('a', preflabel, auth_control=False)
                        auth.fields.append(datafield)
                    except:
                        print(f"Could not assign {preflabel} to 550 as a narrower term")
                        pass
        
    # English pref labels go in 150
    for f150 in g.objects(URIRef(uri), SKOS.prefLabel):
        field = Datafield(tag=lang_tags_map[f150.language]['prefLabel'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f150)
        auth.fields.append(field)

    # English alt labels go in 450
    for f450 in g.objects(URIRef(uri), SKOS.altLabel):
        field = Datafield(tag=lang_tags_map[f450.language]['altLabel'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f450)
        auth.fields.append(field)

    # English scope notes go in 680
    for f680 in g.objects(URIRef(uri), SKOS.scopeNote):
        field = Datafield(tag=lang_tags_map[f680.language]['scopeNote'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f680)
        auth.fields.append(field)

    # 688? 

    # English general/source notes go in 670, other langs in 933-937
    for f670 in g.objects(URIRef(uri), SKOS.note):
        field = Datafield(tag=lang_tags_map[f670.language]['note'], record_type='auth')
        field.ind1 = ' '
        field.ind2 = ' '
        field.set('a', f670)
        auth.fields.append(field)

    auth.set_008()
    
    return auth.to_mrc()

def merged(left, right):
    # We keep what's in the left document and overwrite whatever is in the right document
    auth = Auth()
    auth.id = left.id

    # find all the tags that are in the right (SKOS)
    skos_tags = right.get_tags()

    # and all the tags in the left (original MARC)
    original_tags = left.get_tags()

    # copy the original, because we're gonna subtract
    keep_tags = original_tags

    # Subbtract the skos tags from the original tags and store them in what we're keeping
    for st in skos_tags:
        if st in keep_tags:
            keep_tags.remove(st)

    # process the left side of the record (what we're keeping)
    for tag in keep_tags:
        this_fields = left.get_fields(tag)
        for field in this_fields:
            auth.fields.append(field)

    # process the right side of the record (the incoming values from the SKOS)
    for tag in skos_tags:
        this_fields = right.get_fields(tag)
        for field in this_fields:
            auth.fields.append(field)
    
    return auth