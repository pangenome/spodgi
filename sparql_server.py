#!/usr/bin/python3
from flask import Flask, request, jsonify, Response, g
from spodgi import OdgiStore
import click
import sys
import json

import rdflib
from rdflib.namespace import RDF
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin

def resultformat_to_mime(format): 
    if format=='xml': return "application/sparql-results+xml"
    if format=='json': return "application/sparql-results+json"
    if format=='html': return "text/html"
    return "text/plain"

def get_format_and_mimetype(accept_headers, output_format):

    if not output_format:
        output_format = "xml"
        if "text/html" in accept_headers:
            output_format = "html"
        if "application/sparql-results+json" in accept_headers:
            output_format = "json"
        
    mimetype = resultformat_to_mime(output_format)
    mimetype = request.values.get("force-accept", mimetype)

    return output_format, mimetype

app = Flask(__name__)
spodgi = None
@app.route('/sparql')
def sparql_endpoint():
    query = request.args.get('query')

    accept_headers = request.headers["Accept"]
    output_format = request.values.get("output", None)

    output_format, mimetype = get_format_and_mimetype(accept_headers, output_format)

    res = spodgi.query(query).serialize(format = output_format)
    
    response = Response(res)
    response.headers["Content-Type"] = mimetype
    return response
@click.command()
@click.argument('odgifile')
@click.option('--base', default='http://example.org/vg/')
def main(odgifile, base):
    global spodgi
    plugin.register('OdgiStore', Store,'spodgi.OdgiStore', 'OdgiStore')
    store = plugin.get('OdgiStore', Store)(base=base)
    spodgi = Graph(store=store)
    spodgi.open(odgifile, create=False)
    app.run(host='0.0.0.0',port=5001)

if __name__ == '__main__':
    main()
