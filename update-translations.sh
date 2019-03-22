#!/bin/sh
source ./venv/bin/activate
pybabel extract -F metadata/babel.cfg -o metadata/messages.pot ./metadata
pybabel update -i metadata/messages.pot -d metadata/translations
pybabel compile -d metadata/translations

echo "If you still need to translate strings, be sure to run this script again once you're done."
