import boto3
from flask_babel import gettext

class CONFIG(object):

    client = boto3.client('ssm')
    connect_string = client.get_parameter(Name='undhl-issu-connect')['Parameter']['Value']

    INIT = {
        'title': gettext(u'UNBIS Thesaurus'),
        'uri_base': 'http://metadata.un.org/thesaurus/',
        #'thesaurus_pattern': '/thesaurus/%s' % PROJECT_ID,
        #'project_pattern': '/projects/%s' % PROJECT_ID    
    }