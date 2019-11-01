#!/usr/bin/python3
import odgi
import rdflib
import click
import io
import pprint
from spodgi import OdgiStore
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin
    
@click.command()
@click.argument('odgifile')
@click.argument('ttl', type=click.File('wb'))
@click.option('--base', default='http://example.org/vg/')
@click.option('--syntax', default='ntriples')
def main(odgifile, ttl, base, syntax):
    plugin.register('OdgiStore', Store,'spodgi.OdgiStore', 'OdgiStore')
    store=plugin.get('OdgiStore', Store)(base=base)
    spodgi = Graph(store=store)
    spodgi.open(odgifile, create=False)
    res = spodgi.serialize(ttl, syntax)
    spodgi.close()

if __name__ == "__main__":
    main()
