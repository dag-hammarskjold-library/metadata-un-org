from metadata.config import GRAPH

class Term:
    '''
    Generic class for a single instance of a specified RDF Type.

    Used in all views of a single Term, including serialization.

    Also allows predicate whitelisting to control output.
    '''
    def __init__(self, uri, definition, lang='en'):
        self.uri = uri
        self.lang = lang
        self.definition = definition