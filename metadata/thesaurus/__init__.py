from flask import Blueprint

thesaurus_app = Blueprint('thesaurus', __name__, template_folder='templates', static_folder='static')

from metadata.thesaurus import routes