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
from spodgi.term import StepIriRef, NodeIriRef, StepBeginIriRef, StepEndIriRef

VG = Namespace('http://biohackathon.org/resource/vg#')
FALDO = Namespace('http://biohackathon.org/resource/faldo#')

knownTypes = [VG.Node, VG.Path, VG.Step, FALDO.Region, FALDO.ExactPosition, FALDO.Position]
knownPredicates = [RDF.value, VG.rank, VG.position, VG.step, VG.path, VG.linksForwardToForward,
                   VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse, VG.links,
                   VG.reverseOfNode, VG.node, FALDO.begin, FALDO.end, FALDO.reference, FALDO.position]
nodeRelatedPredicates = [VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward,
                         VG.linksReverseToReverse, VG.links, RDF.value]
stepAssociatedTypes = [FALDO.Region, FALDO.ExactPosition, FALDO.Position, VG.Step]
stepAssociatedPredicates = [VG.rank, VG.position, VG.path, VG.node, VG.reverseOfNode, FALDO.begin, FALDO.end,
                            FALDO.reference, FALDO.position]

__all__ = ['OdgiStore']


# This is the code that can be passed into the C++ handle graph.
# However, my worry is how to change this so that this can be an generator
# on the python side?
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
        if self.subject is None or self.subject == pathIri:
            # given at RDF.type and the VG.Path as obj we can generate the matching triple
            if (self.predicate is None or self.predicate == RDF.type) and (self.obj is None or self.obj == VG.Path):
                self.li.append([(pathIri, RDF.type, VG.Path), None])
            if self.predicate is None or self.predicate == RDFS.label:
                label = rdflib.term.Literal(pathName)
                # if the label does not match the obj we should generate a triple here
                if self.obj is None or self.obj == label:
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
        if base is None:
            self.base = 'http://example.org/vg/'
        else:
            self.base = base
        self.pathNS = Namespace(f'{self.base}path/')
        self.stepNS = Namespace(f'{self.base}step/')
        self.bind('path', self.pathNS)
        self.bind('step', self.stepNS)
        self.odgi = None

    def open(self, odgifile, create=False):
        og = odgi.graph()
        ogf = og.load(odgifile)
        self.odgi = og

    def triples(self, triple_pattern, context=None):
        """A generator over all the triples matching """
        subject, predicate, obj = triple_pattern
        if RDF.type == predicate and obj is not None:
            return self.typeTriples(subject, predicate, obj)
        elif predicate in nodeRelatedPredicates:
            return self.nodes(subject, predicate, obj)
        elif predicate in stepAssociatedPredicates:
            return self.steps(subject, predicate, obj)
        elif RDFS.label == predicate:
            return self.paths(subject, predicate, obj)
        elif subject is None and predicate is None and obj is None:
            return chain(self.__allPredicates(), self.__allTypes())
        elif subject is not None:
            subjectIriParts = subject.toPython().split('/')
            if 'node' == subjectIriParts[-2] and self.odgi.has_node(int(subjectIriParts[-1])):
                handle = self.odgi.get_handle(int(subjectIriParts[-1]))
                return chain(self.handleToTriples(predicate, obj, handle),
                             self.handleToEdgeTriples(subject, predicate, obj, handle))
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

    # For the known types we can shortcut evaluation in many cases
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
            yield from self.triples((None, RDF.type, typ))

    def __allPredicates(self):
        for pred in knownPredicates:
            yield from self.triples((None, pred, None))

    @staticmethod
    def __emptygen():
        """return an empty generator"""
        if False:
            yield

    def nodes(self, subject, predicate, obj):
        if subject is not None:
            isNodeIri = self.isNodeIriInGraph(subject)

            if predicate == RDF.type and obj == VG.Node and isNodeIri:
                yield [(subject, RDF.type, VG.Node), None]
            elif predicate is None and obj == VG.Node and isNodeIri:
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
        if type(iri) == NodeIriRef:
            return True
        else:
            iri_parts = iri.toPython().split('/')
            return 'node' == iri_parts[-2] and self.odgi.has_node(int(iri_parts[-1]))

    def paths(self, subject, predicate, obj):
        li = []
        tt = PathToTriples(self.odgi, self.pathNS, subject, predicate, obj, li)
        self.odgi.for_each_path_handle(tt)
        for p in li:
            yield p

    def steps(self, subject, predicate, obj):

        if subject is None:
            for pathHandle in self.pathHandles():
                if not self.odgi.is_empty(pathHandle):
                    rank = 1
                    position = 1
                    step_handle = self.odgi.path_begin(pathHandle)
                    node_handle = self.odgi.get_handle_of_step(step_handle)
                    yield from self.stepHandleToTriples(step_handle, subject, predicate, obj, node_handle=node_handle,
                                                        rank=rank, position=position)

                    while self.odgi.has_next_step(step_handle):
                        step_handle = self.odgi.get_next_step(step_handle)
                        position = position + self.odgi.get_length(node_handle)
                        node_handle = self.odgi.get_handle_of_step(step_handle)
                        rank = rank + 1
                        yield from self.stepHandleToTriples(step_handle, subject, predicate, obj,
                                                            node_handle=node_handle,
                                                            rank=rank, position=position)
        elif type(subject) == StepIriRef:
            yield from self.stepHandleToTriples(subject.step_handle, subject, predicate, obj, rank=subject.rank(),
                                                position=subject.position())
        elif type(subject) == StepBeginIriRef:
            yield from self.stepHandleToTriples(subject.step_handle, subject, predicate, obj, rank=subject.rank(),
                                                position=subject.position())
        elif type(subject) == StepEndIriRef:
            yield from self.stepHandleToTriples(subject.step_handle, subject, predicate, obj, rank=subject.rank(),
                                                position=subject.position())
        else:
            subject_iri_parts = subject.toPython().split('/')
            if 'path' == subject_iri_parts[-4] and 'step' == subject_iri_parts[-2]:
                path_name = subject_iri_parts[-3];
                pathHandle = self.odgi.get_path_handle(path_name)
                stepRank = int(subject_iri_parts[-1]);

                if not self.odgi.is_empty(pathHandle):
                    rank = 1
                    position = 1
                    step_handle = self.odgi.path_begin(pathHandle)
                    node_handle = self.odgi.get_handle_of_step(step_handle)
                    while rank != stepRank and self.odgi.has_next_step(step_handle):
                        rank = rank + 1
                        position = position + self.odgi.get_length(node_handle)
                        step_handle = self.odgi.get_next_step(step_handle)
                        node_handle = self.odgi.get_handle_of_step(step_handle)
                    yield from self.stepHandleToTriples(step_handle, subject, predicate, obj, node_handle=node_handle,
                                                        rank=rank, position=position)

    # else:
    # for nodeHandle in self.handles():
    # for stepHandle in self.odgi.steps_of_handle(nodeHandle, False):
    # yield from self.stepHandleToTriples(stepHandle, subject, predicate, obj, nodeHandle=nodeHandle)
    def stepHandleToTriples(self, stepHandle, subject, predicate, obj, node_handle=None, rank=None, position=None):

        if type(subject) == StepIriRef:
            step_iri = subject
        elif type(subject) == StepBeginIriRef:
            step_iri = subject._stepIri
        elif type(subject) == StepEndIriRef:
            step_iri = subject._stepIri
        else:
            step_iri = StepIriRef(stepHandle, self.base, self.odgi, position, rank)

        if subject is None or step_iri == subject:
            if predicate == RDF.type or predicate is None:
                if obj is None or obj == VG.Step:
                    yield ([(step_iri, RDF.type, VG.Step), None])
                if obj is None or obj == FALDO.Region:
                    yield ([(step_iri, RDF.type, FALDO.Region), None])
            if node_handle is None:
                node_handle = self.odgi.get_handle_of_step(stepHandle)
            node_iri = NodeIriRef(node_handle, odgi=self.odgi, base=self.base)
            if (predicate == VG.node or predicate is None and not self.odgi.get_is_reverse(node_handle)) and (
                    obj is None or node_iri == obj):
                yield ([(step_iri, VG.node, node_iri), None])

            if (predicate == VG.reverseOfNode or predicate is None and self.odgi.get_is_reverse(node_handle)) and (
                    obj is None or node_iri == obj):
                yield ([(step_iri, VG.reverseOfNode, node_iri), None])

            if (predicate == VG.rank or predicate is None) and rank is not None:
                rank = Literal(rank)
                if obj is None or obj == rank:
                    yield ([(step_iri, VG.rank, rank), None])

            if (predicate == VG.position or predicate is None) and position is not None:
                position = Literal(position)
                if obj is None or position == obj:
                    yield ([(step_iri, VG.position, position), None])

            if predicate == VG.path or predicate is None:
                path = self.odgi.get_path_handle_of_step(stepHandle)
                path_name = self.odgi.get_path_name(path)

                path_iri = self.pathNS.term(f'{path_name}')
                if obj is None or path_iri == obj:
                    yield ([(step_iri, VG.path, path_iri), None])

            if predicate is None or predicate == FALDO.begin:
                yield ([(step_iri, FALDO.begin, StepBeginIriRef(step_iri)), None])

            if predicate is None or predicate == FALDO.end:
                yield ([(step_iri, FALDO.end, StepEndIriRef(step_iri)), None])

            if subject is None:
                begin = StepBeginIriRef(step_iri)
                yield from self.faldoForStep(step_iri, begin, predicate, obj)
                end = StepEndIriRef(step_iri)
                yield from self.faldoForStep(step_iri, end, predicate, obj)

        if (type(subject) == StepBeginIriRef) and step_iri == subject._stepIri:
            yield from self.faldoForStep(subject._stepIri, subject, predicate, obj)
        elif type(subject) == StepEndIriRef and step_iri == subject._stepIri:
            yield from self.faldoForStep(subject._stepIri, subject, predicate, obj)

    def faldoForStep(self, step_iri, subject, predicate, obj):
        ep = Literal(subject.position())
        if (predicate is None or predicate == FALDO.position) and (obj is None or obj == ep):
            yield ([(subject, FALDO.position, ep), None])
        if (predicate is None or predicate == RDF.type) and (obj is None or obj == FALDO.ExactPosition):
            yield ([(subject, RDF.type, FALDO.ExactPosition), None])
        if (predicate is None or predicate == RDF.type) and (obj is None or obj == FALDO.Position):
            yield ([(subject, RDF.type, FALDO.Position), None])
        if predicate is None or predicate == FALDO.reference:
            path = step_iri.path()
            pathName = self.odgi.get_path_name(path)
            pathIri = self.pathNS.term(f'{pathName}')
            if obj is None or obj == pathIri:
                yield ([(subject, FALDO.reference, pathIri), None])

    def handleToTriples(self, predicate, obj, node_handle):
        node_iri = NodeIriRef(node_handle, odgi=self.odgi, base=self.base)

        if predicate == RDF.value or predicate is None:
            seq_value = rdflib.term.Literal(self.odgi.get_sequence(node_handle))
            if obj is None or obj == seq_value:
                yield [(node_iri, RDF.value, seq_value), None]
        elif (predicate == RDF.type or predicate is None) and (obj is None or obj == VG.Node):
            yield [(node_iri, RDF.type, VG.Node), None]

    def handleToEdgeTriples(self, subject, predicate, obj, nodeHandle):

        if predicate is None or (predicate in nodeRelatedPredicates):
            to_node_handles = []
            self.odgi.follow_edges(nodeHandle, False, CollectEdges(to_node_handles));
            node_iri = NodeIriRef(nodeHandle, odgi=self.odgi, base=self.base)
            for edge in to_node_handles:

                otherIri = NodeIriRef(edge, odgi=self.odgi, base=self.base)

                if obj is None or otherIri == obj:
                    node_is_reverse = self.odgi.get_is_reverse(nodeHandle);
                    other_is_reverse = self.odgi.get_is_reverse(edge)
                    # TODO: check the logic here
                    if (
                            predicate is None or VG.linksForwardToForward == predicate) and not node_is_reverse and not other_is_reverse:
                        yield ([(node_iri, VG.linksForwardToForward, otherIri), None])
                    if (
                            predicate is None or VG.linksReverseToForward == predicate) and node_is_reverse and not other_is_reverse:
                        yield ([(node_iri, VG.linksReverseToForward, otherIri), None])
                    if (
                            predicate is None or VG.linksReverseToReverse == predicate) and node_is_reverse and other_is_reverse:
                        yield ([(node_iri, VG.linksReverseToReverse, otherIri), None])
                    if (
                            predicate is None or VG.linksReverseToReverse == predicate) and not node_is_reverse and other_is_reverse:
                        yield ([(node_iri, VG.linksForwardToReverse, otherIri), None])
                    if predicate is None or VG.links == predicate:
                        yield ([(node_iri, VG.links, otherIri), None])

    def bind(self, prefix, namespace):
        self.namespace_manager.bind(prefix, namespace)

    def namespace(self, search_prefix):
        for prefix, namespace in self.namespace_manager.namespaces():
            if search_prefix == prefix:
                return namespace

    def prefix(self, searchNamespace):
        for prefix, namespace in self.namespace_manager.namespaces():
            if searchNamespace == namespace:
                return prefix

    def namespaces(self):
        return self.namespace_manager.namespaces()

    def handles(self):
        node_id = self.odgi.min_node_id()

        max_node_id = self.odgi.max_node_id()
        while node_id <= max_node_id:
            if self.odgi.has_node(node_id):
                node_id = node_id + 1
                yield self.odgi.get_handle(node_id - 1)

    def pathHandles(self):
        paths = []
        self.odgi.for_each_path_handle(CollectPaths(paths))
        yield from paths
