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

class NodeToPattern:
    def __init__(self, og, base, predicate):
        self.og = og
        self.base = base
        self.predicate = predicate;

    def __call__(self, handle):
        nodeId = self.og.get_id(handle);
        nodeIri = rdflib.term.URIRef(f'{self.base}node/{nodeId}')
    
        if (predicate == RDF.value):
            seqValue = rdflib.term.Literal(self.og.get_sequence(handle))
            yield [(nodeIri, predicate, seqvalue), None]
        
        

class OdgiStore(Store):
    """\
    An in memory implementation of an ODGI read only store.
    
    Authors: Jerven Bolleman
    """
    
    def __init__(self, configuration=None, identifier=None):
        super(OdgiStore, self).__init__(configuration)
        self.identifier = identifier
        if not configuration == None:
            self.base = configuration.base
        else:
            self.base = 'http://example.org/'
        
    def open(self, odgifile, create=False):
        og = odgi.graph()
        ogf = og.load(odgifile)
        self.odgi = og

    def triples(self, triple_pattern, context=None):
        """A generator over all the triples matching """
        subject, predicate, object = triple_pattern
        
        if RDF.type == predicate and object != ANY:
            if not knownTypes.__contains__(object):
                return self.__emptygen()
            elif VG.Node == object:
                if subject != ANY:
                    subjectIriParts = subject.toPython().split('/')
                    if 'node' == subjectIriParts[-2] and self.odgi.has_node(int(subjectIriParts[-1])):
                        yield [(subject, predicate, object), None]
                else:
                    print("""We need to return all the nodes""")
                    return self.nodeToTriples(predicate, self.nodes)
    
    def __emptygen(self):
        """return an empty generator"""
        if False:
            yield
    
    def nodeToTriples(self, predicate, nodes):
        print('nodeToTriples')
        for node in nodes:
            nodeIri = rdflib.term.URIRef(f'{self.base}node/{self.odgi.get_id}')
            if (predicate == RDF.value):
                seqValue = rdflib.term.Literal(self.odgi.get_sequence(handle))
                yield [(nodeIri, predicate, seqvalue), None]
            elif(predicate == RDF.type):
                yield [(nodeIri, RDF.type, VG.Node), None]
    
    def nodes():
        print('nodes')
        nodeId = self.odgi.min_node_id
        maxNodeId = self.odgi.max_node_id
        while (nodeId <= maxNodeId):
            if(self.odgi.has_node(nodeId)):
                yield self.odgi.get_node(nodeId)
                nodeId+1 
