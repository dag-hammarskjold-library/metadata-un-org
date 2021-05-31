from flask import Blueprint, render_template, redirect, url_for, request, jsonify, abort, json, Response, abort
from flask_babel import Babel, gettext
from flask_accept import accept
import re

from metadata.graphs.thesaurus.config import Config
from metadata.graphs.thesaurus import model
from metadata.graphs.thesaurus.model import Thesaurus, Domain, MicroThesaurus, Concept, Breadcrumb

thesaurus_app = Blueprint('thesaurus', __name__, template_folder='templates', static_folder='static', cli_group='thesaurus')

from metadata.graphs.thesaurus.commands import *

def get_match_class_by_regex(match_classes, pattern):
    return(next(filter(lambda m: re.compile(m['regex']).match(pattern),match_classes), None))

@thesaurus_app.route('/')
@accept('text/html')
def index():
    return "foo"

@thesaurus_app.route('/<id>')
@accept('text/html')
def get_by_id(id):
    
    try:
        this_class = get_match_class_by_regex(Config.match_classes,id)
        class_name = this_class['name']
        about_uri = Config.uri_base + str(id)
        fetch_uri = request.host_url + '/thesaurus/' + str(id)
    except:
        abort(404)
    
    return render_template(f'thesaurus_{class_name}.html', about=about_uri, fetch=fetch_uri, **Config.global_kwargs)

@get_by_id.support('application/ld+json')
def get_json(id):
    try:
        this_class = get_match_class_by_regex(Config.match_classes,id)
        class_name = this_class['name']
        this_uri = Config.uri_base + str(id)
    except:
        abort(404)

    this_resource = getattr(model, class_name)(this_uri)
    this_g = this_resource.graph

    json_data = this_g.serialize(format='json-ld', context=Config.jsonld_context)

    return json_data