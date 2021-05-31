from metadata.graphs import thesaurus
from metadata.graphs.thesaurus.utils import tcode
from metadata.graphs.thesaurus import thesaurus_app
from metadata.graphs.thesaurus.config import Config
import click, os

@thesaurus_app.cli.command('reload-concept')
@click.argument('uri')
def reload_concept(uri):
    pass

@thesaurus_app.cli.command('upsert-marc')
@click.argument('uri')
def upsert_marc(uri):
    pass