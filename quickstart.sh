echo "Starting $1 environment"

source venv/bin/activate
export FLASK_APP="metadata"
export FLASK_ENV="$1"
flask run -p 5001 --reload