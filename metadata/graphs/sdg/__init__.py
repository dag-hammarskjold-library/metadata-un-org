from flask import Blueprint

sdg_app = Blueprint('sdg', __name__, template_folder='templates', static_folder='static', cli_group='sdg')

from metadata.graphs.sdg.commands import *

@sdg_app.route('/')
def index():
    return "foo"