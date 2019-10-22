from mongoengine import connect
from metadata.lib.ppmdb import Concept, Label, Relationship, reload_concept
from metadata.lib.poolparty import PoolParty, Thesaurus
from metadata.sdg.config import CONFIG
import ssl

connect(host=CONFIG.connect_string, db=CONFIG.db_name, ssl_cert_reqs=ssl.CERT_NONE)
pool_party = PoolParty(CONFIG.endpoint, CONFIG.project_id, CONFIG.username, CONFIG.password)
thesaurus = Thesaurus(pool_party)

def get_or_update(uri):
    '''
    First try getting from the database. If that fails, reload from PoolParty
    '''
    try:
        concept = Concept.objects.get(uri=uri)
        return concept
    except:
        reload_true = reload_concept(uri, thesaurus)
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