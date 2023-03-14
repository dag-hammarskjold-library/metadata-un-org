from flask import Flask, request
from flask_babel import Babel, gettext
from metadata.config import GLOBAL_CONFIG

LANGUAGES = GLOBAL_CONFIG.LANGUAGES

app = Flask(__name__, static_folder='static', template_folder='templates')
babel = Babel(app)
#cache.init_app(app)

@babel.localeselector
def get_locale():
    locale = request.args.get('lang',request.accept_languages.best_match(LANGUAGES.keys()))
    #print(locale)
    return locale

from metadata.routes import *

# Use this section to register your sub-applications.
from metadata.thesaurus import thesaurus_app
app.register_blueprint(thesaurus_app, url_prefix='/thesaurus', title='UNBIS Thesaurus')

from metadata.sdg import sdg_app
app.register_blueprint(sdg_app, url_prefix='/sdg', title='Sustainable Development Goals Taxonomy')

app.launched = ['thesaurus','sdg']