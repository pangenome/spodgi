#!/usr/bin/python3
import xg
import rdflib
import click
import io
import pprint
from spodgi import XgStore

from rdflib.namespace import RDF
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin

@click.command()
@click.argument('xgfile')
@click.argument('sparql')
@click.option('--base', default='http://example.org/vg/')
@click.option('--syntax', default='turtle')
def main(xgfile, sparql, base, syntax):
    
    plugin.register('XgStore', Store,'spodgi.XgStore', 'XgStore')
    s = plugin.get('XgStore', Store)(base=base)
    spodgi = Graph(store=s)
    spodgi.open(xgfile, create=False)
    res = spodgi.query(sparql)
    
    for row in res:
        print(row)
    spodgi.close()

if __name__ == "__main__":
    main()

