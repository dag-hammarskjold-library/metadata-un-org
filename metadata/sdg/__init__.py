from flask import Blueprint
from metadata.sdg.config import CONFIG

sdg_app = Blueprint(CONFIG.INIT['blueprint_name'], __name__, template_folder='templates', static_folder='static')

from metadata.sdg import routes