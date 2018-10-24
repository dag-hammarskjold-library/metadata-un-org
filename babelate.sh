#!/bin/sh
source ./venv/bin/activate
pybabel extract -F metadata/babel.cfg -o metadata/messages.pot ./metadata
pybabel init -i metadata/messages.pot -d metadata/translations -l ar
pybabel init -i metadata/messages.pot -d metadata/translations -l zh
pybabel init -i metadata/messages.pot -d metadata/translations -l en
pybabel init -i metadata/messages.pot -d metadata/translations -l fr
pybabel init -i metadata/messages.pot -d metadata/translations -l ru
pybabel init -i metadata/messages.pot -d metadata/translations -l es
