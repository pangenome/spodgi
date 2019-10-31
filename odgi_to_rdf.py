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
    

class ToTurtle:
    def __init__(self, og, base):
        self.og = og
        self.base = base

    def __call__(self, handle):
        nodeId = self.og.get_id(handle);
        nodeIri = rdflib.term.URIRef(f'{self.base}node/{nodeId}')
        seqValue = rdflib.term.Literal(self.og.get_sequence(handle))
        
        pprint.pprint((nodeIri, RDF.value, seqValue))


@click.command()
@click.argument('odgifile')
@click.argument('ttl', type=click.File('wb'))
@click.option('--base', default='http://example.org/')
@click.option('--syntax', default='ntriples')
def main(odgifile, ttl, base, syntax):
    plugin.register('OdgiStore', Store,'spodgi.OdgiStore', 'OdgiStore')
    spodgi = Graph(store='OdgiStore')
    spodgi.open(odgifile, create=False)
    res = spodgi.serialize(ttl, syntax)
    
    spodgi.close()
    

if __name__ == "__main__":
    main()

