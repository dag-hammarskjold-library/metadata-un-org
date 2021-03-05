from flask import Blueprint
import click

thesaurus_app = Blueprint('thesaurus', __name__, template_folder='templates', static_folder='static', cli_group='thesaurus')

from metadata.lib.ppmdb import *
@thesaurus_app.cli.command('foo')
def foo():
    print("bar")


from metadata.thesaurus import routes
