#!/usr/bin/python3
import odgi
import rdflib
import click
import io
import pprint
from spodgi import OdgiStore

from rdflib.namespace import RDF
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin

@click.command()
@click.argument('odgifile')
@click.argument('sparql')
@click.option('--base', default='http://example.org/')
@click.option('--syntax', default='turtle')
def main(odgifile, sparql, base, syntax):
    
    plugin.register('OdgiStore', Store,'spodgi.OdgiStore', 'OdgiStore')
    print(plugin.get('OdgiStore', Store))
    spodgi = Graph(store='OdgiStore')
    spodgi.open(odgifile, create=False)
    spodgi.query(sparql)
    spodgi.close()

if __name__ == "__main__":
    main()

