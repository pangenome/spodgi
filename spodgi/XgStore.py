#!/usr/bin/python3
import xg
import rdflib
import io
from rdflib.namespace import RDF, RDFS, NamespaceManager, Namespace
from rdflib.store import Store
from rdflib.term import Literal
from rdflib import Graph
from rdflib import plugin
from itertools import chain

VG = Namespace('http://biohackathon.org/resource/vg#')

knownTypes = [VG.Node, VG.Path, VG.Step]
knownPredicates = [RDF.value, VG.rank, VG.offset, VG.step, VG.path, VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse, VG.reverseOfNode, VG.node]
linkPredicates = [VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse]

__all__ = [ 'XgStore' ]

ANY = Any = None

#This is the code that can be passed into the C++ handle graph.
#However, my worry is how to change this so that this can be an generator
#on the python side?
class PathToTriples:
    def __init__(self, xg, pathNS, subject, predicate, obj, li):
        self.xg = xg
        self.pathNS = pathNS
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.li = li;

    # Generate the triples for the pathHandles that match the triple_pattern passed in
    def __call__(self, pathHandle):
        pathName = self.xg.get_path_name(pathHandle);
        pathIri = self.pathNS.term(f'{pathName}')
        # if any path is ok or this path then generate triples else skip.
        if (self.subject == ANY or self.subject == pathIri):
            #given at RDF.type and the VG.Path as obj we can generate the matching triple
            if ((self.predicate == ANY or self.predicate == RDF.type) and (self.obj == ANY or self.obj == VG.Path)):
                self.li.append([(pathIri, RDF.type, VG.Path), None])
            if (self.predicate == ANY or self.predicate == RDFS.label):
                label = rdflib.term.Literal(pathName)
                # if the label does not match the obj we should generate a triple here
                if (self.obj == ANY or self.obj == label):
                    self.li.append([(pathIri, RDFS.label, label), None])

class CollectEdges:
    def __init__(self, edges):
        self.edges = edges
        
    def __call__(self, edgeHandle):
        self.edges.append(edgeHandle)
        
class CollectPaths:
    def __init__(self, paths):
        self.paths = paths
        
    def __call__(self, pathHandle):
        self.paths.append(pathHandle)

class XgStore(Store):
    
    """\
    An in memory implementation of an ODGI read only store.
    
    It used the disk based xg/handlegraph as backing store.
    
    Authors: Jerven Bolleman
    """
    
    def __init__(self, configuration=None, identifier=None, base=None):
        super(XgStore, self).__init__(configuration)
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
        
    def open(self, xgfile, create=False):
        oxg = xg.graph()
        oxgf = oxg.load(xgfile)
        self.xg = oxg

    def triples(self, triple_pattern, context=None):
        """A generator over all the triples matching """
        subject, predicate, obj = triple_pattern
        if RDF.type == predicate and obj != ANY:
            if not knownTypes.__contains__(obj):
                return self.__emptygen()
            elif VG.Node == obj:
                return self.nodes(subject, predicate, obj)
            elif VG.Path == obj:
                return self.paths(subject, predicate, obj)
            elif VG.Step == obj:
                return self.steps(subject, predicate, obj)
        elif RDF.value == predicate or linkPredicates.__contains__(predicate):
            return self.nodes(subject, predicate, obj)
        elif VG.node == predicate or VG.rank == predicate or VG.reverseOfNode == predicate or VG.path == predicate:
            return self.steps(subject, predicate, obj)
        elif RDFS.label == predicate:
            return self.paths(subject, predicate, obj)
        elif subject == ANY and predicate == ANY and obj == ANY:
            return chain(self.__allPredicates(), self.__allTypes())
        elif subject != ANY:
            subjectIriParts = subject.toPython().split('/')
            if 'node' == subjectIriParts[-2] and self.xg.has_node(int(subjectIriParts[-1])):
                handle = self.xg.get_handle(int(subjectIriParts[-1]))
                return chain(self.handleToTriples(predicate, obj, handle), self.handleToEdgeTriples(subject, predicate, obj, handle))
            elif 'path' == subjectIriParts[-4] and 'step' == subjectIriParts[-2]:
                return self.steps(subject, predicate, obj)
            elif 'path' == subjectIriParts[-2]:
                return self.paths(subject, predicate, obj)
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
 
    def nodes(self, subject, predicate, obj):
        if subject != ANY:
            isNodeIri = self.isNodeIriInGraph(subject)
            
            if predicate == RDF.type and obj == VG.Node and isNodeIri:
                yield [(subject, RDF.type, VG.Node), None]
            elif predicate == ANY and obj == VG.Node and isNodeIri:
                yield [(subject, RDF.type, VG.Node), None]
            elif (type(subject) == NodeIriRef):
                yield from self.handleToTriples(predicate, obj, subject._nodeHandle)
                yield from self.handleToEdgeTriples(subject, predicate, obj, subject._nodeHandle)
            elif isNodeIri:
                subjectIriParts = subject.toPython().split('/')
                nh = self.xg.get_handle(int(subjectIriParts[-1]))
                yield from self.handleToTriples(predicate, obj, nh)
                yield from self.handleToEdgeTriples(subject, predicate, obj, nh)
            else:
                return self.__emptygen()
        else:
            for handle in self.handles():
                yield from self.handleToEdgeTriples(subject, predicate, obj, handle)
                yield from self.handleToTriples(predicate, obj, handle)

    def isNodeIriInGraph(self, iri):
        if (type(iri) == NodeIriRef):
            return True
        else:
            iriParts = iri.toPython().split('/')
            return 'node' == iriParts[-2] and self.xg.has_node(int(iriParts[-1]))

    def paths(self, subject, predicate, obj):
        li = []
        tt =PathToTriples(self.xg, self.pathNS, subject, predicate,  obj, li)
        self.xg.for_each_path_handle(tt)
        for p in li:
            yield p

    def steps(self, subject, predicate, obj):
        if (subject == Any):
            for pathHandle in self.pathHandles():
                if not self.xg.is_empty(pathHandle):
                    rank=1
                    position=1
                    stepHandle = self.xg.path_begin(pathHandle)
                    nodeHandle = self.xg.get_handle_of_step(stepHandle)
                    yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle, rank=rank,position=position)
                    
                    while self.xg.has_next_step(stepHandle):
                        stepHandle = self.xg.get_next_step(stepHandle)
                        position = position + self.xg.get_length(nodeHandle)
                        nodeHandle = self.xg.get_handle_of_step(stepHandle)
                        rank = rank + 1
                        yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle, rank=rank, position=position)
        elif (type(subject) == StepIriRef):
            yield from self.stepHandleToTriples(subject.stepHandle(), subject, predicate, obj, rank=subject.rank(), position=subject.position())
        else:
            subjectIriParts = subject.toPython().split('/')
            if 'path' == subjectIriParts[-4] and 'step' == subjectIriParts[-2]:
                pathName = subjectIriParts[-3];
                pathHandle = self.xg.get_path_handle(pathName)
                stepRank = int(subjectIriParts[-1]);
                
                if not self.xg.is_empty(pathHandle):     
                    rank=1
                    position=1
                    stepHandle = self.xg.path_begin(pathHandle)
                    nodeHandle = self.xg.get_handle_of_step(stepHandle)
                    while rank != stepRank and self.xg.has_next_step(stepHandle):
                        rank = rank +1
                        position = position + self.xg.get_length(nodeHandle)
                        stepHandle = self.xg.get_next_step(stepHandle)
                        nodeHandle = self.xg.get_handle_of_step(stepHandle)
                    yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle, rank=rank, position=position)
                        
                    
                    
    #else:
            #for nodeHandle in self.handles():
                #for stepHandle in self.xg.steps_of_handle(nodeHandle, False):
                    #yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle)
    
    def stepHandleToTriples(self, stepHandle, subject, predicate, obj, nodeHandle=None, rank=None,position=None):
        
        path = self.xg.get_path_handle_of_step(stepHandle)
        pathName = self.xg.get_path_name(path)
        if (type(subject) == StepIriRef):
            stepIri = subject
        else:
            stepIri = StepIriRef(stepHandle, self.base, self.xg, position, rank)
        if (subject == ANY or stepIri == subject):
            if (predicate == RDF.type or predicate == ANY) and (obj == ANY or obj == VG.Step):
                yield ([(stepIri, RDF.type, VG.Step), None])
            if (nodeHandle == None):
                nodeHandle = self.xg.get_handle_of_step(stepHandle)
            nodeIri = self.nodeIri(nodeHandle)
            if (predicate == VG.node or predicate == ANY and not self.xg.get_is_reverse(nodeHandle)) and (obj == ANY or nodeIri == obj):
                yield ([(stepIri, VG.node, nodeIri), None])
                
            if (predicate == VG.reverseOfNode or predicate == ANY and self.xg.get_is_reverse(nodeHandle)) and (obj == ANY or nodeIri == obj):
                yield ([(stepIri, VG.reverseOfNode, nodeIri), None])
        
            if (predicate == VG.rank or predicate == ANY) and not rank == None:
                
                rank = Literal(rank)
                if obj == Any or obj == rank:
                    yield ([(stepIri, VG.rank, rank), None])    
            if (predicate == VG.position or predicate == ANY) and not position == None:
                
                position = Literal(position)
                if obj == Any or position == obj:
                    yield ([(stepIri, VG.position, position), None])
            if (predicate == VG.path or predicate == ANY):
                pathIri = self.pathNS.term(f'{pathName}')
                if obj == Any or pathIri == obj:
                    yield ([(stepIri, VG.path, pathIri), None])

    def handleToTriples(self, predicate, obj, handle):
        nodeIri = self.nodeIri(handle)
        
        if (predicate == RDF.value or predicate == ANY):
            seqValue = rdflib.term.Literal(self.xg.get_sequence(handle))
            if (obj == Any or obj == seqValue):
                yield [(nodeIri, RDF.value, seqValue), None]
        elif (predicate == RDF.type or predicate == ANY) and (obj == Any or obj == VG.Node):
            yield [(nodeIri, RDF.type, VG.Node), None]
            
    def handleToEdgeTriples(self, subject, predicate, obj, handle):
        
        if predicate == ANY or linkPredicates.__contains__(predicate):
            edges = []
            self.xg.follow_edges(handle, False, CollectEdges(edges));
            nodeIri = self.nodeIri(handle)
            for edge in edges:
                
                otherIri = self.nodeIri(edge)
                
                if (obj == Any or otherIri == obj):
                    nodeIsReverse = self.xg.get_is_reverse(handle);
                    otherIsReverse = self.xg.get_is_reverse(edge)
                    #TODO: check the logic here
                    if (predicate == ANY or VG.linksForwardToForward == predicate) and not nodeIsReverse and not otherIsReverse:
                        yield ([(nodeIri, VG.linksForwardToForward, otherIri), None])
                    elif (predicate == ANY or VG.linksReverseToForward == predicate) and nodeIsReverse and not otherIsReverse:
                        yield ([(nodeIri, VG.linksReverseToForward, otherIri), None])
                    elif (predicate == ANY or VG.linksReverseToReverse == predicate) and nodeIsReverse and otherIsReverse:
                        yield ([(nodeIri, VG.linksReverseToReverse, otherIri), None])
                    elif (predicate == ANY or VG.linksReverseToReverse == predicate) and not nodeIsReverse and otherIsReverse:
                        yield ([(nodeIri, VG.linksForwardToReverse, otherIri), None])
   
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
        return NodeIriRef(nodeHandle, self.nodeNS, self.xg)
        
    
    def handles(self):
        nodeId = self.xg.min_node_id()
        
        maxNodeId = self.xg.max_node_id()
        while (nodeId <= maxNodeId):
            if(self.xg.has_node(nodeId)):
                nodeId=nodeId+1 
                yield self.xg.get_handle(nodeId-1)

    def pathHandles(self):
        paths = []
        self.xg.for_each_path_handle(CollectPaths(paths))
        yield from paths
    
class NodeIriRef(rdflib.term.Identifier):
    __slots__ = ("_nodeHandle", "_base", "_xg")
    
    def __new__(cls, nodeHandle, base, xg):
         inst =  str.__new__(cls)
         inst._nodeHandle = nodeHandle
         inst._base = base
         inst._xg = xg
         return inst
      
    def __eq__(self, other):
        if type(self) == type(other):
            return self._xg.get_id(self._nodeHandle) == self._xg.get_id(other._nodeHandle) and self._base == other._base
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
                return self._xg.get_id(self._nodeHandle) > self._xg.get_id(other._nodeHandle)
            
    def n3(self, namespace_manager = None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'
    
    def toPython(self):
        return self.unicode()
        
    def unicode(self):
        return f'{self._base}{self._xg.get_id(self._nodeHandle)}'
    
    def __str__(self):
        return self.unicode()
    
    def __repr__(self):
        return 'xg.NodeIriRef(\''+self.unicode()+'\')'

    def __hash__(self):
        return self._xg.get_id(self._nodeHandle)

class StepIriRef(rdflib.term.Identifier):
    __slots__ = ("_stepHandle", "_base", "_xg", "_position", "_rank")
    
    def __new__(cls, stepHandle, base, xg, position, rank):
         inst =  str.__new__(cls)
         inst._stepHandle = stepHandle
         inst._base = base
         inst._xg = xg
         inst._rank = rank
         inst._position = position
         return inst
      
    def __eq__(self, other):
        
        if type(self) == type(other):
            return self._stepHandle == other._stepHandle and self._base == other._base
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
                return self._rank > other._rank
            
    def n3(self, namespace_manager = None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def stepHandle(self):
        return self._stepHandle
    
    def rank(self):
        return self._rank
    
    def position(self):
        return self._position
    
    def path(self):
        return self._path
        
    def toPython(self):
        return self.unicode()
        
    def unicode(self):
        return f'{self._base}path/{self._xg.get_path_name(self._xg.get_path_handle_of_step(self._stepHandle))}/step/{self._rank}'
    
    def __str__(self):
        return self.unicode()
    
    def __repr__(self):
        return 'xg.StepIriRef(\''+self.unicode()+'\')'

    def __hash__(self):
        return hash(self._stepHandle)
