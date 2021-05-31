from flask import Blueprint

thesaurus_app = Blueprint('thesaurus', __name__, template_folder='templates', static_folder='static', cli_group='thesaurus')

from metadata.graphs.thesaurus.commands import *

@thesaurus_app.route('/')
def index():
    return "foo"