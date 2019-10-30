#!/usr/bin/python3
import odgi
import rdflib
import io
from rdflib.namespace import RDF, RDFS
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin
from itertools import chain
VG = rdflib.Namespace('http://biohackathon.org/resource/vg#')

knownTypes = [VG.Node, VG.Path, VG.Step]
knownPredicates = [RDF.value, VG.rank, VG.offset, VG.step, VG.path, VG.linksForwardToForward, VG.node]

__all__ = [ 'OdgiStore' ]

ANY = Any = None

#This is the code that can be passed into the C++ handle graph.
#However, my worry is how to change this so that this can be an generator
#on the python side?
class PathToTriples:
    def __init__(self, og, base, subject, predicate, object, li):
        self.odgi = og
        self.base = base
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.li = li;

    def __call__(self, pathHandle):
        pathName = self.odgi.get_path_name(pathHandle);
        pathIri = rdflib.term.URIRef(f'{self.base}path/{pathName}')
        if (self.subject == ANY or self.subject == pathIri):
            if (self.predicate == ANY or self.predicate == RDF.type):
                self.li.append([(pathIri, RDF.type, VG.Path), None])
            if (self.predicate == ANY or self.predicate == RDFS.label):
                label = rdflib.term.Literal(pathName)
                self.li.append([(pathIri, RDFS.label, label), None])

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
                return self.nodes(subject, predicate, object)
            elif VG.Path == object:
                return self.paths(subject, predicate, object)
            elif VG.Step == object:
                return self.steps(subject, predicate, object)
        elif RDF.value == predicate:
            return self.nodes(subject, predicate, object)
        elif VG.node == predicate:
            return self.steps(subject, VG.node, object)
        elif RDFS.label == predicate:
            return self.paths(subject, predicate, object)
        elif subject == ANY and predicate == ANY and object == ANY:
            return chain(self.__allPredicates(), self.__allTypes())
            #for pred in knowPredicates:
                #yield self.triples((ANY, pred, ANY))
        else:
            return self.__emptygen()
                     
    def __allTypes(self):
        # This needs to return the combination of all types. For now it just does the first one :(
        for type in knownTypes:
            yield from self.triples((ANY, RDF.type, type))
            
    def __allPredicates(self):
        # This needs to return the combination of all predicates. For now it just does the first one :(
        for pred in knownPredicates:
            yield from self.triples((ANY, pred, ANY))
            
    def __emptygen(self):
        """return an empty generator"""
        if False:
            yield
 
    def nodes(self, subject, predicate, object):
        if subject != ANY:
            subjectIriParts = subject.toPython().split('/')
            if predicate == RDF.type and object == VG.Node and 'node' == subjectIriParts[-2] and self.odgi.has_node(int(subjectIriParts[-1])):
                yield [(subject, predicate, object), None]
            elif predicate == ANY and object == VG.Node and 'node' == subjectIriParts[-2] and self.odgi.has_node(int(subjectIriParts[-1])):
                yield [(subject, predicate, object), None]
            elif 'node' == subjectIriParts[-2] and self.odgi.has_node(int(subjectIriParts[-1])):
                yield self.handleToTriples(predicate, self.odgi.get_handle(int(subjectIriParts[-1])))
            else:
                return self.__emptygen()
        else:
            for handle in self.handles():
                yield self.handleToTriples(predicate, handle)

    def paths(self, subject, predicate, object):
        li = []
        tt =PathToTriples(self.odgi, self.base, subject, predicate,  object, li)
        self.odgi.for_each_path_handle(tt)
        for p in li:
            yield p

    def steps(self, subject, predicate, object):
        for handle in self.handles():
            nodeIri = rdflib.term.URIRef(f'{self.base}node/{self.odgi.get_id(handle)}')
            for stepHandle in self.odgi.steps_of_handle(handle, False):
                path = self.odgi.get_path_handle_of_step(stepHandle)
                pathName = self.odgi.get_path_name(path)
                print(stepHandle.first())
                print(stepHandle.second())
                stepIri = rdflib.term.URIRef(f'{self.base}step/{pathName}-{self.odgi.get_id(handle)}')
                
                if (predicate == RDF.type):
                    yield [(stepIri, RDF.type, VG.Node), None]
                elif (predicate == VG.node):
                    yield [(stepIri, VG.node, nodeIri), None]
                

    def handleToTriples(self, predicate, handle):
        nodeIri = rdflib.term.URIRef(f'{self.base}node/{self.odgi.get_id(handle)}')
        if (predicate == RDF.value):
            seqValue = rdflib.term.Literal(self.odgi.get_sequence(handle))
            return [(nodeIri, predicate, seqValue), None]
        elif (predicate == RDF.type):
            return [(nodeIri, RDF.type, VG.Node), None]
        elif predicate == VG.linksForwardToForward:
            # TODO: figure out what I can get  from a handle
            return None;
                  
    
    def handles(self):
        nodeId = self.odgi.min_node_id()
        maxNodeId = self.odgi.max_node_id()
        while (nodeId < maxNodeId):
            if(self.odgi.has_node(nodeId)):
                nodeId=nodeId+1 
                yield self.odgi.get_handle(nodeId)
        return

    def pathHandles(self):
        return
