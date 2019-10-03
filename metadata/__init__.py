from flask import Flask, request
from metadata.cache import cache
from flask_babel import Babel, gettext
from .config import GLOBAL_CONFIG

LANGUAGES = GLOBAL_CONFIG.LANGUAGES

app = Flask(__name__)
babel = Babel(app)
cache.init_app(app)

@babel.localeselector
def get_locale():
    locale = request.args.get('lang',request.accept_languages.best_match(LANGUAGES.keys()))
    print(locale)
    return locale

# Use this section to register your sub-applications.
from metadata.thesaurus import thesaurus_app
app.register_blueprint(thesaurus_app, url_prefix='/thesaurus', title=gettext(u'UNBIS Thesaurus'))

from metadata.unnames import unnames_app
app.register_blueprint(unnames_app, url_prefix='/unnames', title=gettext(u'UN System Names'))

from metadata import routes
