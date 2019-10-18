#!/usr/bin/python3
import odgi
import rdflib
import click
import io
import pprint
from rdflib.namespace import RDF

vg = rdflib.Namespace('http://biohackathon.org/resource/vg#')
vg.node
    

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
def main(odgifile, ttl, base):
    og = odgi.graph()
    ogf = og.load(odgifile)
    ogo = og.optimize(ogf)
    og.for_each_handle(ToTurtle(og, base))
    

if __name__ == "__main__":
    main()

