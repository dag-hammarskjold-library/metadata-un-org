from mongoengine import StringField, DictField, URLField, ListField, EmbeddedDocument, Document, EmbeddedDocumentListField, DateTimeField
import time, json, re
from urllib.parse import quote
from metadata.lib.gsparql import build_graph
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from rdflib.namespace import SKOS, DC, DCTERMS, FOAF, DOAP
from rdflib.term import URIRef, Literal, BNode
from pprint import pprint
from flatten_dict import flatten

# This is a collection of classes for interfacing with
# some MongoDB models representing RDF data.

class Label(EmbeddedDocument):
    label = StringField(required=True)
    language = StringField()

    meta = {
        'indexes': [
            {
                'fields': ['label','language'],
                'unique': True
            }
        ]
    }

class Relationship(EmbeddedDocument):
    predicate = URLField(required=True)
    object = ListField(required=True)

class Breadcrumb(EmbeddedDocument):
    breadcrumb = DictField()
    language = StringField()

class Concept(Document):
    uri = URLField(required=True, unique=True)
    pref_labels = EmbeddedDocumentListField(Label)
    alt_labels = EmbeddedDocumentListField(Label)
    scope_notes = EmbeddedDocumentListField(Label)
    breadcrumbs = EmbeddedDocumentListField(Breadcrumb)
    rdf_properties = EmbeddedDocumentListField(Relationship)
    created = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    updated = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

    def get_breadcrumb_by_uri(self, uri):
        return next(filter(lambda r: r['breadcrumb']['uri'] == uri, self.breadcrumbs))

    def get_property_by_predicate(self,predicate):
        return next(filter(lambda r: r['predicate'] == predicate, self.rdf_properties),None)

    def get_property_values_by_predicate(self, predicate, lang=None):
        return_data = []
        try:
            values = getattr(self, predicate)
            if lang is not None:
                value = next(filter(lambda v: v.language == lang, values),None)
                return_data = value
            return_data = values
        except:
            for r in self.rdf_properties:
                if r.predicate == predicate:
                    if lang is not None:
                        if r.object['language'] == lang:
                            return_data = r.object
                    else:
                        return_data = r.object
        return return_data

    def pref_label(self, lang='en'):
        return next(filter(lambda x: x['language'] == lang, self.pref_labels),None)

    def get_labels(self, label_type, lang):
        return_data = []
        for label in getattr(self, label_type):
            if label.language == lang:
                return_data.append(label)
        return return_data

    def to_json(self):
        pref_labels = []
        alt_labels = []
        scope_notes = []
        rdf_properties = []
        return_data = {
            'uri': self.uri,
            'pref_labels': pref_labels,
            'alt_labels': alt_labels,
            'scope_notes': scope_notes,
            'rdf_properties': rdf_properties
        }

        for label in self.pref_labels:
            pref_labels.append({
                'label': label.label,
                'language': label.language
            })
        return_data['pref_labels'] = pref_labels

        for label in self.alt_labels:
            pref_labels.append({
                'label': label.label,
                'language': label.language
            })
        return_data['alt_labels'] = alt_labels
        
        for label in self.scope_notes:
            pref_labels.append({
                'label': label.label,
                'language': label.language
            })
        return_data['scope_notes'] = scope_notes

        for prop in self.rdf_properties:
            rdf_properties.append({
                'predicate': prop.predicate,
                'object': prop.object
            })
        return_data['rdf_properties'] = rdf_properties
        return json.dumps(return_data)

'''
All of the stuff below is mainly for working with Thesaurus data. It should be moved.
'''

def build_concept_path(graph, uri):
    # get the broader terms for this URI, where broader could be
    # SKOS.broader OR SKOS.topConceptOf; these are mutually exclusive.
    broaders = graph.objects(URIRef(uri), SKOS.broader|SKOS.topConceptOf)

    these_b = []

    for broader in broaders:
        # broaders is a generator. Once we finish iterating, it will be empty,
        # but we still want what's in it.
        these_b.append(broader)
        broader_graph = build_graph(str(broader))
        # Add the contents of broader_graph to the original graph so we can 
        # keep querying up the chain
        graph = graph + broader_graph

    # We're gonna call this same function again until we run out of broader terms.
    return {
        'uri': uri,
        'broaders': [build_concept_path(graph=graph, uri=str(broader)) for broader in these_b]
    }

def sublist(my_list):
    if my_list:
        yield my_list
        yield from sublist(my_list[:-2])

def reload_concept(uri, languages):
    '''
    This is a replacement method for a deprecated method of the same name.
    It takes a URI, builds a graph from gsparql, then uses that
    to write the results to the database.
    '''

    print("Deleting %s" % uri)
    try:
        concept = Concept.objects.get(uri=uri)
        #print(concept.to_json())
        #concept.delete()
    except:
        print('Nothing found...')
        pass


    concept = Concept(uri=uri)
    print("Reloading %s" % uri)

    concept_graph = build_graph(uri)
    #print(concept_graph.serialize(format='json-ld'))

    pref_labels = concept_graph.preferredLabel(URIRef(uri))
    for pl in pref_labels:
        concept.pref_labels.append(Label(
            label = pl[1],
            language = pl[1].language
        ))
    
    alt_labels = concept_graph.objects(subject=URIRef(uri), predicate=SKOS.altLabel)
    for al in alt_labels:
        concept.alt_labels.append(Label(
            label = al,
            language = al.language
        ))

    scope_notes = concept_graph.objects(subject=URIRef(uri), predicate=SKOS.scopeNote)
    for sn in scope_notes:
        concept.scope_notes.append(Label(
            label = sn,
            language = sn.language
        ))

    relationships = {}
    concept_relationships = []
    got_properties = concept_graph.predicate_objects(subject=URIRef(uri))
    for prop in got_properties:
        predicate = str(prop[0])
        this_prop = {}

        lang = getattr(prop[1], 'language', None)
        if lang is not None:
            this_prop['label'] = str(prop[1])
            this_prop['language'] = prop[1].language
        else:
            if '://' not in str(prop[1]):
                this_prop['label'] = str(prop[1])
            else:
                if 'lib-thesaurus' in str(prop[1]):
                    this_prop['label'] = str(prop[1])
                else:
                    this_prop['uri'] = str(prop[1])

        if predicate in relationships:
            relationships[predicate].append(this_prop)
        else:
            relationships[predicate] = []
            relationships[predicate].append(this_prop)

    for k in relationships.keys():
        this_r = Relationship(predicate=k, object=relationships[k])
        concept.rdf_properties.append(this_r)

    if languages is None:
        languages = ['en']

    concept_path = build_concept_path(graph=concept_graph, uri=uri)
    paths = flatten(concept_path, reducer='dot', enumerate_types=(list,))
    path_keys = sorted(paths.keys(), key=lambda x: len(x), reverse=True)
    base_keys = []
    for pk in path_keys:
        base_keys.append(".".join(pk.split(".")[:-1]))

    reconstructed_paths = {}
    for bk in base_keys:
        if len(bk) > 3:
            path_list = sublist(bk.split("."))
            reconstructed_paths[bk] = []
            for path in path_list:
                this_key = f"{'.'.join(path)}.uri"
                this_uri = paths[this_key]
                reconstructed_paths[bk].append(this_uri)
            reconstructed_paths[bk].append(uri)
    
    for rp in reconstructed_paths:
        hierarchy = reconstructed_paths[rp]
        if len(hierarchy[0].split('/')[-1]) == 2:
            # this is a domain and we can proceed with this hierarchy
            this_domain = hierarchy.pop(0)
            for language in languages:
                domain_graph = build_graph(this_domain)
                this_bc = {
                    'uri': this_domain,
                    'identifier': this_domain.split('/')[-1],
                    'label': domain_graph.preferredLabel(URIRef(this_domain), lang=language)[0][1],
                    'conceptPath': []
                }
                for h in hierarchy:
                    this_g = build_graph(h)
                    this_id = h.split("/")[-1]
                    if len(this_id) == 6:
                        this_cp = {
                            'uri': h,
                            'label': this_g.preferredLabel(URIRef(h), lang=language)[0][1],
                            'identifier': '.'.join(re.findall(r'.{1,2}', this_id))
                        }
                    else:
                        this_cp = {
                            'uri': h,
                            'label': this_g.preferredLabel(URIRef(h), lang=language)[0][1]
                        }
                    this_bc['conceptPath'].append(this_cp)
                concept.breadcrumbs.append(Breadcrumb(breadcrumb=this_bc, language=language))
        else:
            next

    for bc in concept.breadcrumbs:
        print(bc.breadcrumb)

    print(concept.to_json())