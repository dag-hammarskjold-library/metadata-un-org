from flask import Flask, request
from flask_babel import Babel, gettext
from .config import LANGUAGES

app = Flask(__name__)
babel = Babel(app)

from metadata.thesaurus import thesaurus_app
#from metadata.undo import undo_app
app.register_blueprint(thesaurus_app, url_prefix='/thesaurus', title=gettext('UNBIS Thesaurus'))
#app.register_blueprint(undo_app, url_prefix='/undo')

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())

from metadata import routes