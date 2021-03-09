from flask import Blueprint

thesaurus_app = Blueprint('thesaurus', __name__, template_folder='templates', static_folder='static', cli_group='thesaurus')

from metadata.thesaurus.commands import *

from metadata.thesaurus import routes