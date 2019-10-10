import requests, json
from metadata import cache

'''
This is a VERY light library to interface with PoolParty and only implements a
small subset of the larger API. 
'''

class PoolParty(object):
    '''
    This is the main class for handling a PoolParty connection and interacting 
    with the subclasses, such as Thesaurus.
    '''

    def __init__(self, endpoint, project_id, username, password):
        self.endpoint = endpoint
        self.project_id = project_id
        self.auth = (username, password)

    def get_data(self, url):
        #print(url)
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return_data = json.loads(response.text)
            return return_data
        else:
            return None

    
class Thesaurus(object):

    def __init__(self, pool_party):
        self.endpoint = pool_party.endpoint + '/thesaurus/' + pool_party.project_id
        self.pool_party = pool_party

    @cache.memoize()
    def get_broaders(self, concept, properties=None, language=None, transitive=None, workflowStatus=None):
        '''
        Returns a list of broader concepts for a concept
        '''
        api_url = self.endpoint + '/broaders?concept=' + concept

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if transitive is not None:
            api_url = api_url + '&transitive=' + transitive

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_child_concepts(self, parent, properties=None, language=None, transitive=None, workflowStatus=None):
        '''
        Returns a list of child concepts for a concept or concept scheme. This 
        method covers both: /narrowers and /topconcepts and also retrieves the 
        URIs of semantic relations
        '''
        api_url = self.endpoint + '/childconcepts?parent=' + parent

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if transitive is not None:
            api_url = api_url + '&transitive=' + transitive

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_concept(self, concept, properties=None, language=None, workflowStatus=None):
        '''
        Returns a JSON representation of the concept
        '''
        api_url = self.endpoint + '/concept?concept=' + concept

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_concepts(self, concepts, properties=None, language=None, workflowStatus=None):
        '''
        Returns JSON representations of the concepts
        '''
        api_url = self.endpoint + '/concepts?concept=' + concepts

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_narrowers(self, concept, properties=None, language=None, transitive=None, workflowStatus=None):
        '''Returns a list of narrower concepts for a concept'''
        api_url = self.endpoint + '/narrowers?concept=' + concept

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if transitive is not None:
            api_url = api_url + '&transitive=' + transitive

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_paths(self, concept, properties=None, language=None, defaultLanguageAsFallback=None, workflowStatus=None):
        '''
        Returns a list of paths from the concept scheme to the given concept. 
        The list always starts with a concept scheme, with the title as 
        preferred label
        '''
        api_url = self.endpoint + '/paths?concept=' + concept

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if defaultLanguageAsFallback is not None:
            api_url = api_url + '&defaultLanguageAsFallback=' + defaultLanguageAsFallback

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_relateds(self, concept, properties=None, language=None, transitive=None, workflowStatus=None):
        '''Returns a list of related concepts for a concept'''
        api_url = self.endpoint + '/relateds?concept=' + concept

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if transitive is not None:
            api_url = api_url + '&transitive=' + transitive

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()    
    def get_schemes(self, properties=None, language=None):
        '''Returns a list of all concept schemes in the given project'''
        api_url = self.endpoint + '/schemes'

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_subtree(self, root, properties=None, language=None, workflowStatus=None):
        '''
        Returns the subtree of all narrower concepts with the provided concept 
        as root
        '''
        api_url = self.endpoint + '/subtree?root=' + root

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_top_concepts(self, scheme, properties=None, language=None, workflowStatus=None):
        '''
        Returns a list of direct top concepts for a concept scheme
        '''
        api_url = self.endpoint + '/topconcepts?scheme=' + scheme

        if properties is not None:
            api_url = api_url + '&properties=' + ','.join(properties)

        if language is not None:
            api_url = api_url + '&language=' + language

        if workflowStatus is not None:
            api_url = api_url + '&workflowStatus=' + workflowStatus

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_properties(self, resource):
        '''Returns a list of all properties of the given resource'''
        api_url = self.endpoint + '/properties?resource=' + resource

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_property_values(self, resource, prop):
        '''Returns a list of all values for the given property of the given resource'''
        api_url = self.endpoint + '/propertyValues?resource=' + resource + '&property=' + prop

        return_data = self.pool_party.get_data(api_url)
        return return_data

    @cache.memoize()
    def get_types(self, resource):
        '''Returns a list of all rdf:types for the given resource'''
        api_url = self.endpoint + '/types?resource=' + resource

        return_data = self.pool_party.get_data(api_url)
        return return_data