from urllib.parse import quote_plus
import requests

# We just want terms that have lost their URIs from the Central Database
prod_api_url = 'https://td1ljyw4rd.execute-api.us-east-1.amazonaws.com/prod/api/marc/auths/records?start=1&limit=400&search=150__a%3A*%20AND%20072__a%3A*%20AND%20NOT%20035__a%3A%2F%5Ehttp%2F'

# SPARQL read endpoint: 
sparql_e = "http://metadata.un.org:7200/repositories/UNBIST_core?query="

json_data = requests.get(prod_api_url).json()["data"]

unmatched = []
print("PREFIX dct: <http://purl.org/dc/terms/>")
for record in json_data:
    record_data = requests.get(record).json()["data"]
    record_id = record_data["_id"]
    prefLabel = record_data["150"][0]["subfields"][0]["value"]

    sparql_q = 'PREFIX skos: <http://www.w3.org/2004/02/skos/core#> select * where { ?uri skos:prefLabel "' + prefLabel + '"@en . } '

    uri = requests.get(f'{sparql_e}{quote_plus(sparql_q)}', headers={'Accept':'application/json'})
    
    try:
        record_uri = uri.json()["results"]["bindings"][0]["uri"]["value"]
    except IndexError:
        record_uri = None
    
    #print(record_id, prefLabel, record_uri)
    if record_uri is None:
        unmatched.append({"id":record_id, "label": prefLabel})
    else:
        #sparql_u = 'INSERT DATA { GRAPH <http://metadata.un.org/thesaurus> { <' + record_uri + '> dct:identifier "auths:' + str(record_id) + '" } } ;'
        #print(sparql_u)
        cmd = f'flask thesaurus upsert-marc {record_uri} --id {str(record_id)} --test'
        print(cmd)

    
#print(unmatched)