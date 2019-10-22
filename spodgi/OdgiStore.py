#!/usr/bin/python3
import odgi
import rdflib
import io
from rdflib.namespace import RDF
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin
VG = rdflib.Namespace('http://biohackathon.org/resource/vg#')

knownTypes = [VG.Node, VG.Path, VG.Step]

__all__ = [ 'OdgiStore' ]

ANY = Any = None

class ToTurtle:
    def __init__(self, og, base, format):
        self.og = og
        self.base = base
        self.format = format

    def __call__(self, handle):
        nodeId = self.og.get_id(handle);
        nodeIri = rdflib.term.URIRef(f'{self.base}node/{nodeId}')
        seqValue = rdflib.term.Literal(self.og.get_sequence(handle))
        
        pprint.pprint((nodeIri, RDF.value, seqValue))
        pprint.pprint((nodeIri, RDF.type, VG.Node))

class OdgiStore(Store):
    """\
    An in memory implementation of an ODGI read only store.
    
    Authors: Jerven Bolleman
    """
    
    def __init__(self, configuration=None, identifier=None):
        super(OdgiStore, self).__init__(configuration)
        self.identifier = identifier
        
    def open(self, odgifile, create=False):
        og = odgi.graph()
        ogf = og.load(odgifile)
        self.odgi = og

    def triples(self, triple_pattern, context=None):
        """A generator over all the triples matching """
        subject, predicate, object = triple_pattern
        print(predicate == RDF.type)
        print(object)
        if RDF.type == predicate and object != ANY:
            if not knownTypes.__contains__(object):
                return self.__emptygen()
            elif VG.Node == object and subject != ANY and subject.contains('/node/'):
                yield (subject, predicate, object)
            elif VG.Node == object:
                """We need to return all the nodes"""
                return self.iterate_from(odgi.for_each_handle(toTriple(self.odgi, base, syntax)))
    
    def __emptygen(self):
        """return an empty generator"""
        if False:
            yield
