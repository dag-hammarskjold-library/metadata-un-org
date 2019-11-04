from mongoengine import StringField, DictField, URLField, ListField, EmbeddedDocument, Document, EmbeddedDocumentListField, DateTimeField
import time, json
from urllib.parse import quote

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
    
def reload_concept(uri, thesaurus, languages=None):
    '''
    This takes a metadata.lib.poolparty.Thesaurus object as an argument and
    will reload a specific Concept from PoolParty.
    '''
    try:
        concept = Concept.objects.get(uri=uri)
        concept.delete()
    except:
        pass
        
    concept = Concept(uri=uri)
    print(uri)

    got_concept = thesaurus.get_concept(uri, properties=['all'])
    if got_concept is None:
        return False

    pref_labels = thesaurus.get_property_values(uri,'skos:prefLabel')['values']
    for pl in pref_labels:
        concept.pref_labels.append(Label(
            label = pl['label'],
            language = pl['language']
        ))

    alt_labels = thesaurus.get_property_values(uri,'skos:altLabel')['values']
    for al in alt_labels:
        concept.alt_labels.append(Label(
            label = al['label'],
            language = al['language']
        ))

    scope_notes = thesaurus.get_property_values(uri, 'skos:scopeNote')['values']
    for sn in scope_notes:
        concept.scope_notes.append(Label(
            label = sn['label'],
            language = sn['language']
        ))

    if languages is None:
        languages = ['en']
    
    for language in languages:
        breadcrumbs = thesaurus.get_paths(uri, properties=['all'], language=language)

        #print(breadcrumbs)
    
        for breadcrumb in breadcrumbs:
            #print(breadcrumb['conceptScheme'])
            this_breadcrumb = {
                'domain': {
                    'uri': breadcrumb['conceptScheme']['uri'],
                    'identifier': breadcrumb['conceptScheme']['uri'].split('/')[-1],
                    'label': breadcrumb['conceptScheme']['title'],
                    'conceptPath': []
                }
            }
            for cp in breadcrumb['conceptPath']:
                this_cp = {
                    'uri': cp['uri'],
                    'label': cp['prefLabel']
                }
                #print(cp['properties'])
                try:
                    this_identifier = cp['properties']['http://purl.org/dc/elements/1.1/identifier'][0]
                except:
                    this_identifier = None
                if this_identifier is not None:
                    this_cp['identifier'] = this_identifier
                this_breadcrumb['domain']['conceptPath'].append(this_cp)

            #print(this_breadcrumb)

            found_bc = next(filter(lambda x: x.breadcrumb == this_breadcrumb, concept.breadcrumbs),None)
            #print(found_bc)
            if found_bc is None:
                print(this_breadcrumb)
                concept.breadcrumbs.append(Breadcrumb(
                    breadcrumb=this_breadcrumb,
                    language=language
                ))

    relationships = []
    # have to take a different approach with all the props
    got_properties = thesaurus.get_properties(uri)
    for prop in got_properties['properties']:
        property_values = thesaurus.get_property_values(uri,quote(prop['uri']))
        #print(prop['uri'], property_values['values'])
        r = Relationship(str(prop['uri']), property_values['values'])
        relationships.append(r)

    concept.rdf_properties = relationships

    concept.save()
    return concept