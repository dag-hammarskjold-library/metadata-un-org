from flask import Blueprint

sdg_app = Blueprint('sdg', __name__, template_folder='templates', static_folder='static')

from metadata.sdg import routes