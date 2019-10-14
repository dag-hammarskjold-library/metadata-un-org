from mongoengine import StringField, DictField, URLField, ListField, EmbeddedDocument, Document, EmbeddedDocumentListField, DateTimeField
import time

# This is a collection of classes for interfacing with
# some MongoDB models representing RDF data.

class Label(EmbeddedDocument):
    label = StringField(required=True)
    language = StringField()

class Relationship(EmbeddedDocument):
    predicate = URLField(required=True)
    object = DictField(required=True)

class Concept(Document):
    uri = URLField(required=True, unique=True)
    pref_labels = EmbeddedDocumentListField(Label)
    alt_labels = EmbeddedDocumentListField(Label)
    scope_notes = EmbeddedDocumentListField(Label)
    rdf_properties = EmbeddedDocumentListField(Relationship)
    created = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    updated = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

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
                            return_data.append(r.object)
                    else:
                        return_data.append(r.object)
        return return_data

    def pref_label(self, lang='en'):
        return next(filter(lambda x: x['language'] == lang, self.pref_labels),None)

    
def reload_concept(uri, thesaurus):
    '''
    This takes a metadata.lib.poolparty.Thesaurus object as an argument and
    will reload a specific Concept from PoolParty.
    '''
    try:
        concept = Concept.objects.get(uri=uri)
        concept.updated = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    except:
        concept = Concept(uri=uri)

    got_concept = thesaurus.get_concept(uri, properties=['all'])

    pref_labels = thesaurus.get_property_values(uri,'skos:prefLabel')['values']
    for pl in pref_labels:
        concept.pref_labels.append(Label(
            label = pl['label'],
            datatype = pl['datatype'],
            language = pl['language']
        ))

    alt_labels = thesaurus.get_property_values(uri,'skos:altLabel')['values']
    for al in alt_labels:
        concept.alt_labels.append(Label(
            label = al['label'],
            datatype = al['datatype'],
            language = al['language']
        ))

    scope_notes = thesaurus.get_property_values(uri, 'skos:scopeNote')['values']
    for sn in scope_notes:
        concept.scope_notes.append(Label(
            label = sn['label'],
            datatype = sn['datatype'],
            language = sn['language']
        ))

    relationships = []
    for prop in got_concept['properties']:
        #for val in prop:
        r = Relationship(prop, got_concept['properties'][prop])
        relationships.append(r)

    concept.rdf_properties = relationships

    concept.save()
    return 0