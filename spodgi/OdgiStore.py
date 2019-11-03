#!/usr/bin/python3
import odgi
import rdflib
import io
from rdflib.namespace import RDF, RDFS, NamespaceManager, Namespace
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin
from itertools import chain

VG = Namespace('http://biohackathon.org/resource/vg#')

knownTypes = [VG.Node, VG.Path, VG.Step]
knownPredicates = [RDF.value, VG.rank, VG.offset, VG.step, VG.path, VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse, VG.reverseOfNode, VG.node]
linkPredicates = [VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse]

__all__ = [ 'OdgiStore' ]

ANY = Any = None

#This is the code that can be passed into the C++ handle graph.
#However, my worry is how to change this so that this can be an generator
#on the python side?
class PathToTriples:
    def __init__(self, og, pathNS, subject, predicate, object, li):
        self.odgi = og
        self.pathNS = pathNS
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.li = li;

    # Generate the triples for the pathHandles that match the triple_pattern passed in
    def __call__(self, pathHandle):
        pathName = self.odgi.get_path_name(pathHandle);
        pathIri = self.pathNS.term(f'{pathName}')
        # if any path is ok or this path then generate triples else skip.
        if (self.subject == ANY or self.subject == pathIri):
            #given at RDF.type and the VG.Path as object we can generate the matching triple
            if ((self.predicate == ANY or self.predicate == RDF.type) and (self.object == ANY or self.object == VG.Path)):
                self.li.append([(pathIri, RDF.type, VG.Path), None])
            if (self.predicate == ANY or self.predicate == RDFS.label):
                label = rdflib.term.Literal(pathName)
                # if the label does not match the object we should generate a triple here
                if (self.object == ANY or self.object == label):
                    self.li.append([(pathIri, RDFS.label, label), None])

class CollectEdges:
    def __init__(self, edges):
        self.edges = edges
        
    def __call__(self, edgeHandle):
        self.edges.append(edgeHandle)

class OdgiStore(Store):
    
    """\
    An in memory implementation of an ODGI read only store.
    
    It used the disk based odgi/handlegraph as backing store.
    
    Authors: Jerven Bolleman
    """
    
    def __init__(self, configuration=None, identifier=None, base=None):
        super(OdgiStore, self).__init__(configuration)
        self.namespace_manager = NamespaceManager(Graph())
        self.bind('vg', VG)
        self.identifier = identifier
        self.configuration = configuration
        if base == None:
            self.base = 'http://example.org/vg/'
        else:
            self.base = base
        self.nodeNS = Namespace(f'{self.base}node/')
        self.pathNS = Namespace(f'{self.base}path/')
        self.stepNS = Namespace(f'{self.base}step/')
        self.bind('node', self.nodeNS)
        self.bind('path', self.pathNS)
        self.bind('step', self.stepNS)
        
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
        elif RDF.value == predicate or VG.linksForwardToForward == predicate:
            return self.nodes(subject, predicate, object)
        elif VG.node == predicate :
            return self.steps(subject, VG.node, object)
        elif VG.reverseOfNode == predicate :
            return self.steps(subject, VG.reverseOfNode, object)
        elif VG.path == predicate :
            return self.steps(subject, VG.path, object)
        elif RDFS.label == predicate:
            return self.paths(subject, predicate, object)
        elif subject == ANY and predicate == ANY and object == ANY:
            return chain(self.__allPredicates(), self.__allTypes())
        elif subject != ANY:
            subjectIriParts = subject.toPython().split('/')
            if 'node' == subjectIriParts[-2] and self.odgi.has_node(int(subjectIriParts[-1])):
                handle = self.odgi.get_handle(int(subjectIriParts[-1]))
                return  chain(self.handleToTriples(predicate, object, handle), self.handleToEdgeTriples(predicate, object, handle))
            elif 'step' == subjectIriParts[-2]:
                return self.steps(subject, predicate, object)
            elif 'path' == subjectIriParts[-2]:
                return self.paths(subject, predicate, object)
        else:
            return self.__emptygen()
                     
    def __allTypes(self):
        for type in knownTypes:
            yield from self.triples((ANY, RDF.type, type))
            
    def __allPredicates(self):
        for pred in knownPredicates:
            yield from self.triples((ANY, pred, ANY))
            
    def __emptygen(self):
        """return an empty generator"""
        if False:
            yield
 
    def nodes(self, subject, predicate, object):
        if subject != ANY:
            isNodeIri = self.isNodeIriInGraph(subject)
            if predicate == RDF.type and object == VG.Node and isNodeIri:
                yield [(subject, RDF.type, VG.Node), None]
            elif predicate == ANY and object == VG.Node and isNodeIri:
                yield [(subject, RDF.type, VG.Node), None]
            elif isNodeIri:
                yield from self.handleToTriples(predicate, object, self.odgi.get_handle(int(subjectIriParts[-1])))
            else:
                return self.__emptygen()
        else:
            for handle in self.handles():
                yield from self.handleToEdgeTriples(predicate, object, handle)
                yield from self.handleToTriples(predicate, object, handle)

    def isNodeIriInGraph(self, iri):
        iriParts = iri.toPython().split('/')
        return 'node' == iriParts[-2] and self.odgi.has_node(int(iriParts[-1]))

    def paths(self, subject, predicate, object):
        li = []
        tt =PathToTriples(self.odgi, self.pathNS, subject, predicate,  object, li)
        self.odgi.for_each_path_handle(tt)
        for p in li:
            yield p

    def steps(self, subject, predicate, object):
        for handle in self.handles():
            nodeIri = self.nodeIri(handle)
            for stepHandle in self.odgi.steps_of_handle(handle, False):
                path = self.odgi.get_path_handle_of_step(stepHandle)
                pathName = self.odgi.get_path_name(path)
                stepIri = rdflib.URIRef(f'{pathName}-{self.odgi.get_id(handle)}', self.stepNS)
                if (subject == ANY or subject == stepIri):
                    if (predicate == RDF.type or predicate == ANY):
                        yield ([(stepIri, RDF.type, VG.Step), None])
                    if (predicate == VG.node or predicate == ANY and not self.odgi.get_is_reverse(handle)):
                        yield ([(stepIri, VG.node, nodeIri), None])
                    if (predicate == VG.reverseOfNode or predicate == ANY and self.odgi.get_is_reverse(handle)):
                        yield ([(stepIri, VG.reverseOfNode, nodeIri), None])
                    if (predicate == VG.path or predicate == ANY):
                        pathIri = self.pathNS.term(f'{pathName}')
                        yield ([(stepIri, VG.path, pathIri), None])
                

    def handleToTriples(self, predicate, object, handle):
        nodeIri = self.nodeIri(handle)
        if (predicate == RDF.value or predicate == ANY):
            seqValue = rdflib.term.Literal(self.odgi.get_sequence(handle))
            if (object == Any or object == seqValue):
                yield [(nodeIri, RDF.value, seqValue), None]
        elif (predicate == RDF.type or predicate == ANY) and (object == Any or object == VG.Node):
            yield [(nodeIri, RDF.type, VG.Node), None]
            
    def handleToEdgeTriples(self, predicate, object, handle):
        if predicate == ANY or linkPredicates.__contains__(predicate):
            edges = []
            self.odgi.follow_edges(handle, False, CollectEdges(edges));
            nodeIri = self.nodeIri(handle)
            for edge in edges:
                otherNode = self.nodeIri(edge)
                if (object == Any or object == otherIri):
                    nodeIsReverse = self.odgi.get_is_reverse(handle);
                    otherIsReverse = self.odgi.get_is_reverse(edge)
                    #TODO: check the logic here
                    if (predicate == ANY or VG.linksForwardToForward == ANY and not nodeIsReverse and not otherIsReverse):
                        yield ([(nodeIri, VG.linksForwardToForward, otherNode), None])
                    elif (predicate == ANY or VG.linksReverseToForward == ANY and nodeIsReverse and not otherIsReverse):
                        yield ([(nodeIri, VG.linksReverseToForward, otherNode), None])
                    elif (predicate == ANY or VG.linksReverseToReverse == ANY and nodeIsReverse and otherIsReverse):
                        yield ([(nodeIri, VG.linksReverseToReverse, otherNode), None])
                    elif (predicate == ANY or VG.linksReverseToReverse == ANY and not nodeIsReverse and otherIsReverse):
                        yield ([(nodeIri, VG.linksForwardToReverse, otherNode), None])
   
    def bind(self, prefix, namespace):
        self.namespace_manager.bind(prefix, namespace)

    def namespace(self, searchPrefix):
        for prefix, namespace in self.namespace_manager.namespaces():
            if searchPrefix == prefix:
                return namespace

    def prefix(self, searchNamespace):
        for prefix, namespace in self.namespace_manager.namespaces():
            if searchNamespace == namespace:
                return prefix

    def namespaces(self):
        return self.namespace_manager.namespaces()
    
    # This does not make a big difference as numeric local names 
    # are not turned into nice looking shortcuts in turtle 
    def nodeIri(self, nodeHandle):
        return NodeIriRef(nodeHandle, self.nodeNS, self.odgi)
        
    
    def handles(self):
        nodeId = self.odgi.min_node_id()
        
        maxNodeId = self.odgi.max_node_id()
        while (nodeId <= maxNodeId):
            if(self.odgi.has_node(nodeId)):
                nodeId=nodeId+1 
                yield self.odgi.get_handle(nodeId-1)

    def pathHandles(self):
        return
    
class NodeIriRef(rdflib.term.Identifier):
    __slots__ = ("_nodeHandle", "_base", "_odgi")
    
    def __new__(cls, nodeHandle, base, odgi):
         inst =  str.__new__(cls)
         inst._nodeHandle = nodeHandle
         inst._base = base
         inst._odgi = odgi
         return inst
      
    def __eq__(self, other):
        if type(self) == type(other):
            return self._nodeHandle == other._nodeHandle and self._base == other._base
        elif (type(other) == rdflib.URIRef):
            return rdflib.URIRef(self.unicode()) == other
        else:
            return False
                
    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif type(self) == type(other):
            if (self._base > other._base):
                return True
            elif (self._base < other._base):
                return False
            else:
                return self._odgi.get_id(self._nodeHandle) > self._odgi.get_id(other._nodeHandle)
            
    def n3(self, namespace_manager = None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'
    
    def toPython(self):
        return self.unicode()
        
    def unicode(self):
        return f'{self._base}{self._odgi.get_id(self._nodeHandle)}'
    
    def __hash__(self):
        return self._odgi.get_id(self._nodeHandle)
