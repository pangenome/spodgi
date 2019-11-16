#!/usr/bin/python3
import odgi
import rdflib
import io
from rdflib.namespace import RDF, RDFS, NamespaceManager, Namespace
from rdflib.store import Store
from rdflib.term import Literal
from rdflib import Graph
from rdflib import plugin
from itertools import chain
from spodgi.terms import StepIriRef, NodeIriRef, StepIriBeginRef, StepEndIriRef

VG = Namespace('http://biohackathon.org/resource/vg#')
FALDO = Namespace('http://biohackathon.org/resource/faldo#')

knownTypes = [VG.Node, VG.Path, VG.Step, FALDO.Region, FALDO.ExactPosition, FALDO.Position]
knownPredicates = [RDF.value, VG.rank, VG.position, VG.step, VG.path, VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse, VG.links, VG.reverseOfNode, VG.node, FALDO.begin, FALDO.end, FALDO.reference, FALDO.position]
nodeRelatedPredicates = [VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse, VG.links, RDF.value]
stepAssociatedTypes = [FALDO.Region, FALDO.ExactPosition, FALDO.Position]
stepAssociatedPredicates = [VG.rank, VG.position, VG.path, VG.node, VG.reverseOfNode, FALDO.begin, FALDO.end, FALDO.reference, FALDO.position]

__all__ = [ 'OdgiStore' ]

ANY = ANY = None

#This is the code that can be passed into the C++ handle graph.
#However, my worry is how to change this so that this can be an generator
#on the python side?
class PathToTriples:
    def __init__(self, og, pathNS, subject, predicate, obj, li):
        self.odgi = og
        self.pathNS = pathNS
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.li = li;

    # Generate the triples for the pathHandles that match the triple_pattern passed in
    def __call__(self, pathHandle):
        pathName = self.odgi.get_path_name(pathHandle);
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
        self.bind('faldo', FALDO)
        self.identifier = identifier
        self.configuration = configuration
        if base == None:
            self.base = 'http://example.org/vg/'
        else:
            self.base = base
        self.pathNS = Namespace(f'{self.base}path/')
        self.stepNS = Namespace(f'{self.base}step/')
        self.bind('path', self.pathNS)
        self.bind('step', self.stepNS)
        
    def open(self, odgifile, create=False):
        og = odgi.graph()
        ogf = og.load(odgifile)
        self.odgi = og

    def triples(self, triple_pattern, context=None):
        """A generator over all the triples matching """
        subject, predicate, obj = triple_pattern
        if RDF.type == predicate and obj != ANY:
           return self.typeTriples(subject, predicate, obj)
        elif (predicate in nodeRelatedPredicates):
            return self.nodes(subject, predicate, obj)
        elif predicate in stepAssociatedPredicates:
            return self.steps(subject, predicate, obj)
        elif RDFS.label == predicate:
            return self.paths(subject, predicate, obj)
        elif subject == ANY and predicate == ANY and obj == ANY:
            return chain(self.__allPredicates(), self.__allTypes())
        elif subject != ANY:
            subjectIriParts = subject.toPython().split('/')
            if 'node' == subjectIriParts[-2] and self.odgi.has_node(int(subjectIriParts[-1])):
                handle = self.odgi.get_handle(int(subjectIriParts[-1]))
                return chain(self.handleToTriples(predicate, obj, handle), self.handleToEdgeTriples(subject, predicate, obj, handle))
            elif 'path' == subjectIriParts[-4] and 'step' == subjectIriParts[-2]:
                return self.steps(subject, predicate, obj)
            elif 'path' == subjectIriParts[-2]:
                return self.paths(subject, predicate, obj)
            elif type(subject) == StepBeginIriRef or type(subject) == StepEndIriRef:
                return self.steps(subject, predicate, obj)
            else:
                return self.__emptygen()
        else:
            return self.__emptygen()

    #For the known types we can shortcut evaluation in many cases
    def typeTriples(self, subject, predicate, obj):
        if VG.Node == obj:
            return self.nodes(subject, predicate, obj)
        elif VG.Path == obj:
            return self.paths(subject, predicate, obj)
        elif obj in stepAssociatedTypes:
            return self.steps(subject, predicate, obj)
        else:
            return self.__emptygen()

    def __allTypes(self):
        for typ in knownTypes:
            yield from self.triples((ANY, RDF.type, typ))
            
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
                nh = self.odgi.get_handle(int(subjectIriParts[-1]))
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
            return 'node' == iriParts[-2] and self.odgi.has_node(int(iriParts[-1]))

    def paths(self, subject, predicate, obj):
        li = []
        tt =PathToTriples(self.odgi, self.pathNS, subject, predicate,  obj, li)
        self.odgi.for_each_path_handle(tt)
        for p in li:
            yield p

    def steps(self, subject, predicate, obj):
        
        if (subject == ANY):
            for pathHandle in self.pathHandles():
                if not self.odgi.is_empty(pathHandle):
                    rank=1
                    position=1
                    stepHandle = self.odgi.path_begin(pathHandle)
                    nodeHandle = self.odgi.get_handle_of_step(stepHandle)
                    yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle, rank=rank,position=position)
                    
                    while self.odgi.has_next_step(stepHandle):
                        stepHandle = self.odgi.get_next_step(stepHandle)
                        position = position + self.odgi.get_length(nodeHandle)
                        nodeHandle = self.odgi.get_handle_of_step(stepHandle)
                        rank = rank + 1
                        yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle, rank=rank, position=position)
        elif (type(subject) == StepIriRef):
            yield from self.stepHandleToTriples(subject.stepHandle(), subject, predicate, obj, rank=subject.rank(), position=subject.position())
        elif (type(subject) == StepBeginIriRef):
            yield from self.stepHandleToTriples(subject.stepHandle(), subject, predicate, obj, rank=subject.rank(), position=subject.position())
        elif (type(subject) == StepEndIriRef):
            yield from self.stepHandleToTriples(subject.stepHandle(), subject, predicate, obj, rank=subject.rank(), position=subject.position())
        else:
            subjectIriParts = subject.toPython().split('/')
            if 'path' == subjectIriParts[-4] and 'step' == subjectIriParts[-2]:
                pathName = subjectIriParts[-3];
                pathHandle = self.odgi.get_path_handle(pathName)
                stepRank = int(subjectIriParts[-1]);
                
                if not self.odgi.is_empty(pathHandle):     
                    rank=1
                    position=1
                    stepHandle = self.odgi.path_begin(pathHandle)
                    nodeHandle = self.odgi.get_handle_of_step(stepHandle)
                    while rank != stepRank and self.odgi.has_next_step(stepHandle):
                        rank = rank +1
                        position = position + self.odgi.get_length(nodeHandle)
                        stepHandle = self.odgi.get_next_step(stepHandle)
                        nodeHandle = self.odgi.get_handle_of_step(stepHandle)
                    yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle, rank=rank, position=position)
                        
                    
                    
    #else:
            #for nodeHandle in self.handles():
                #for stepHandle in self.odgi.steps_of_handle(nodeHandle, False):
                    #yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle)
    
    def stepHandleToTriples(self, stepHandle, subject, predicate, obj, nodeHandle=None, rank=None,position=None):
        
        if (type(subject) == StepIriRef):
            stepIri = subject
        elif (type(subject) == StepBeginIriRef):
            stepIri = subject._stepIri
        elif (type(subject) == StepEndIriRef):
            stepIri = subject._stepIri
        else:
            stepIri = StepIriRef(stepHandle, self.base, self.odgi, position, rank)

        if (subject == ANY or stepIri == subject):
            if (predicate == RDF.type or predicate == ANY):
                if (obj == ANY or obj == VG.Step):
                    yield ([(stepIri, RDF.type, VG.Step), None])
                if (obj == ANY or obj == FALDO.Region):
                    yield ([(stepIri, RDF.type, FALDO.Region), None])
            if (nodeHandle == None):
                nodeHandle = self.odgi.get_handle_of_step(stepHandle)
            nodeIri = NodeIriRef(nodeHandle, self.odgi, self.base)
            if (predicate == VG.node or predicate == ANY and not self.odgi.get_is_reverse(nodeHandle)) and (obj == ANY or nodeIri == obj):
                yield ([(stepIri, VG.node, nodeIri), None])
                
            if (predicate == VG.reverseOfNode or predicate == ANY and self.odgi.get_is_reverse(nodeHandle)) and (obj == ANY or nodeIri == obj):
                yield ([(stepIri, VG.reverseOfNode, nodeIri), None])
        
            if (predicate == VG.rank or predicate == ANY) and not rank == None:
                rank = Literal(rank)
                if obj == ANY or obj == rank:
                    yield ([(stepIri, VG.rank, rank), None])
                    
            if (predicate == VG.position or predicate == ANY) and not position == None:
                position = Literal(position)
                if obj == ANY or position == obj:
                    yield ([(stepIri, VG.position, position), None])

            if (predicate == VG.path or predicate == ANY):
                path = self.odgi.get_path_handle_of_step(stepHandle)
                pathName = self.odgi.get_path_name(path)

                pathIri = self.pathNS.term(f'{pathName}')
                if obj == ANY or pathIri == obj:
                    yield ([(stepIri, VG.path, pathIri), None])
            
            if (predicate == ANY or predicate == FALDO.begin):
                yield ([(stepIri, FALDO.begin, StepBeginIriRef(stepIri)), None])

            if (predicate == ANY or predicate == FALDO.end):    
                yield ([(stepIri, FALDO.end, StepEndIriRef(stepIri)), None])
                
            if (subject == ANY):
                begin = StepBeginIriRef(stepIri)
                yield from self.faldoForStep(stepIri, begin, predicate, obj)
                end = StepEndIriRef(stepIri)
                yield from self.faldoForStep(stepIri, end, predicate, obj)
        
        if (type(subject) == StepBeginIriRef) and stepIri == subject._stepIri:
            yield from self.faldoForStep(subject._stepIri, subject, predicate, obj)
        elif (type(subject) == StepEndIriRef and stepIri == subject._stepIri):
            yield from self.faldoForStep(subject._stepIri, subject, predicate, obj)
        
    def faldoForStep(self, stepIri, subject, predicate, obj):
        ep = Literal(subject.position())
        if (predicate == ANY or predicate == FALDO.position) and (obj == ANY or obj == ep):
            yield ([(subject, FALDO.position, ep), None])
        if (predicate == ANY or predicate == RDF.type) and (obj == ANY or obj == FALDO.ExactPosition):
            yield ([(subject, RDF.type, FALDO.ExactPosition), None])
        if (predicate == ANY or predicate == RDF.type) and (obj == ANY or obj == FALDO.Position):
            yield ([(subject, RDF.type, FALDO.Position), None])
        if (predicate == ANY or predicate == FALDO.reference):
            path = stepIri.path()
            pathName = self.odgi.get_path_name(path)
            pathIri = self.pathNS.term(f'{pathName}')
            if (obj == ANY or obj == pathIri):
                yield ([(subject, FALDO.reference, pathIri), None])
        

    def handleToTriples(self, predicate, obj, nodeHandle):
        nodeIri = NodeIriRef(nodeHandle, self.odgi, self.base)
        
        if (predicate == RDF.value or predicate == ANY):
            seqValue = rdflib.term.Literal(self.odgi.get_sequence(nodeHandle))
            if (obj == ANY or obj == seqValue):
                yield [(nodeIri, RDF.value, seqValue), None]
        elif (predicate == RDF.type or predicate == ANY) and (obj == ANY or obj == VG.Node):
            yield [(nodeIri, RDF.type, VG.Node), None]
            
    def handleToEdgeTriples(self, subject, predicate, obj, nodeHandle):
        
        if predicate == ANY or (predicate in nodeRelatedPredicates):
            toNodeHandles = []
            self.odgi.follow_edges(nodeHandle, False, CollectEdges(toNodeHandles));
            nodeIri = NodeIriRef(nodeHandle, self.odgi, self.base)
            for edge in toNodeHandles:
                
                otherIri = NodeIriRef(edge, self.odgi, self.base)
                
                if (obj == ANY or otherIri == obj):
                    nodeIsReverse = self.odgi.get_is_reverse(nodeHandle);
                    otherIsReverse = self.odgi.get_is_reverse(edge)
                    #TODO: check the logic here
                    if (predicate == ANY or VG.linksForwardToForward == predicate) and not nodeIsReverse and not otherIsReverse:
                        yield ([(nodeIri, VG.linksForwardToForward, otherIri), None])
                    if (predicate == ANY or VG.linksReverseToForward == predicate) and nodeIsReverse and not otherIsReverse:
                        yield ([(nodeIri, VG.linksReverseToForward, otherIri), None])
                    if (predicate == ANY or VG.linksReverseToReverse == predicate) and nodeIsReverse and otherIsReverse:
                        yield ([(nodeIri, VG.linksReverseToReverse, otherIri), None])
                    if (predicate == ANY or VG.linksReverseToReverse == predicate) and not nodeIsReverse and otherIsReverse:
                        yield ([(nodeIri, VG.linksForwardToReverse, otherIri), None])
                    if (predicate == ANY or VG.links == predicate):
                        yield ([(nodeIri, VG.links, otherIri), None])
   
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
    
    def handles(self):
        nodeId = self.odgi.min_node_id()
        
        maxNodeId = self.odgi.max_node_id()
        while (nodeId <= maxNodeId):
            if(self.odgi.has_node(nodeId)):
                nodeId=nodeId+1 
                yield self.odgi.get_handle(nodeId-1)

    def pathHandles(self):
        paths = []
        self.odgi.for_each_path_handle(CollectPaths(paths))
        yield from paths
    

