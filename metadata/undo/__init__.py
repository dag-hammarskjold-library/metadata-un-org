from flask import Blueprint

undo_app = Blueprint('undo', __name__, template_folder='templates')

from metadata.undo import routes