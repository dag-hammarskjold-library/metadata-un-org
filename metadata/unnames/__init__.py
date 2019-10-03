from flask import Blueprint

unnames_app = Blueprint('unnames', __name__, template_folder='templates', static_folder='static')

from metadata.unnames import routes

