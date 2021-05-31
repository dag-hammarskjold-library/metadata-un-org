from flask import Flask, request
from flask_babel import Babel, gettext
from metadata.config import Config

app = Flask(__name__, static_folder='root/static', template_folder='root/templates')
babel = Babel(app)

@babel.localeselector
def get_locale():
    locale = request.args.get('lang', request.accept_languages.best_match(Config.available_languages))
    return locale

from metadata.root import *
from metadata.commands import *

# Use this section to register and load sub-applications
app.launched = {}

from metadata.graphs.thesaurus import thesaurus_app
app.register_blueprint(thesaurus_app, url_prefix='/thesaurus')
app.launched['thesaurus'] = gettext('UNBIS Thesaurus')

from metadata.graphs.sdg import sdg_app
app.register_blueprint(sdg_app, url_prefix='/sdg')
app.launched['sdg'] = gettext('Sustainable Development Goals')