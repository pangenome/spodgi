#!/usr/bin/python3
import odgi
import rdflib
import io
from rdflib.namespace import RDF, RDFS, NamespaceManager, Namespace
from rdflib.store import Store
from rdflib.term import Literal, URIRef, Identifier, Node, BNode
from rdflib import Graph
from rdflib import plugin
from itertools import chain
from spodgi.term import StepIriRef, NodeIriRef, StepBeginIriRef, StepEndIriRef, PathIriRef
from urllib.parse import urlparse
from typing import List
import re


VG = Namespace('http://biohackathon.org/resource/vg#')
FALDO = Namespace('http://biohackathon.org/resource/faldo#')

knownTypes = [VG.Node, VG.Path, VG.Step, FALDO.Region, FALDO.ExactPosition, FALDO.Position]
knownPredicates = [RDF.value, VG.rank, VG.position, VG.path, VG.linksForwardToForward,
                   VG.linksForwardToReverse, VG.linksReverseToForward, VG.linksReverseToReverse, VG.links,
                   VG.reverseOfNode, VG.node, FALDO.begin, FALDO.end, FALDO.reference, FALDO.position]
nodeRelatedPredicates = [VG.linksForwardToForward, VG.linksForwardToReverse, VG.linksReverseToForward,
                         VG.linksReverseToReverse, VG.links, RDF.value]
stepAssociatedTypes = [FALDO.Region, FALDO.ExactPosition, FALDO.Position, VG.Step]
stepAssociatedPredicates = [VG.rank, VG.position, VG.path, VG.node, VG.reverseOfNode, FALDO.begin, FALDO.end,
                            FALDO.reference, FALDO.position]

__all__ = ['OdgiStore']


class CollectEdges:
    def __init__(self, edges):
        self.edges = edges

    def __call__(self, edge_handle):
        self.edges.append(edge_handle)


class CollectPaths:
    path = re.compile('https?://')
    def __init__(self, paths: List[PathIriRef], odgi_graph: odgi, base: str):
        self.known_paths = paths
        self.odgi_graph = odgi_graph
        self.base = base

    def __call__(self, path_handle):
        name = self.odgi_graph.get_path_name(path_handle)
        try:
            if self.path.match(name):
                result = urlparse(name)
                self.known_paths.append(PathIriRef(name, path_handle))
            else:
                self.known_paths.append(PathIriRef(f'{self.base}path/{name}', path_handle))
        except ValueError:
            self.known_paths.append(PathIriRef(f'{self.base}path/{name}', path_handle))


class OdgiStore(Store):
    """\
    An in memory implementation of an ODGI read only store.
    
    It used the disk based odgi/handlegraph as backing store.
    
    Authors: Jerven Bolleman
    """
    odgi_graph: odgi

    knownPaths: List[PathIriRef] = []
    namespace_manager: NamespaceManager
    base: str

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
        self.odgi_graph = None

    def open(self, odgi_file, create=False):
        og = odgi.graph()
        ogf = og.load(odgi_file)
        self.odgi_graph = og
        self.odgi_graph.for_each_path_handle(CollectPaths(self.knownPaths, self.odgi_graph, self.base))

    def triples(self, triple_pattern, context=None):
        """A generator over all the triples matching """
        subject, predicate, obj = triple_pattern

        """we have no bnodes in our data"""
        if isinstance(subject, BNode) or isinstance(object, BNode):
            return self.__emptygen()
        if RDF.type == predicate and obj is not None:
            return self.type_triples(subject, predicate, obj)
        elif predicate in nodeRelatedPredicates:
            return self.nodes(subject, predicate, obj)
        elif predicate in stepAssociatedPredicates:
            return self.steps(subject, predicate, obj)
        elif RDFS.label == predicate:
            return self.paths(subject, predicate, obj)
        elif subject is None and predicate is None and obj is None:
            return chain(self.nodes(subject, predicate, obj),
                         self.steps(subject, predicate, obj),
                         self.paths(subject, predicate, obj))
        elif subject is not None:
            if type(subject) == PathIriRef:
                return self.paths(subject, predicate, obj)
            elif type(subject) == StepBeginIriRef or type(subject) == StepEndIriRef:
                return self.steps(subject, predicate, obj)
            elif type(subject) == NodeIriRef:
                return self.nodes(subject, predicate, obj)
            elif type(subject) == StepIriRef:
                return self.steps(subject, predicate, obj)

            subject_iri_parts = subject.toPython().split('/')
            if 'node' == subject_iri_parts[-2] and self.odgi_graph.has_node(int(subject_iri_parts[-1])):
                handle = self.odgi_graph.get_handle(int(subject_iri_parts[-1]))
                ns = NodeIriRef(handle, self.odgi_graph, self.base)
                return chain(self.handle_to_triples(predicate, obj, handle),
                             self.handle_to_edge_triples(ns, predicate, obj))
            elif 'path' == subject_iri_parts[-4] and 'step' == subject_iri_parts[-2]:
                return self.steps(subject, predicate, obj)
            elif 'path' == subject_iri_parts[-2]:
                return self.paths(subject, predicate, obj)
            else:
                return self.__emptygen()
        else:
            return self.__emptygen()

    # For the known types we can shortcut evaluation in many cases
    def type_triples(self, subject, predicate, obj):
        if VG.Node == obj:
            return self.nodes(subject, predicate, obj)
        elif VG.Path == obj:
            return self.paths(subject, predicate, obj)
        elif obj in stepAssociatedTypes:
            return self.steps(subject, predicate, obj)
        else:
            return self.__emptygen()

    def __all_types(self):
        for typ in knownTypes:
            yield from self.triples((None, RDF.type, typ))

    def __all_predicates(self):
        for predicate in knownPredicates:
            yield from self.triples((None, predicate, None))

    @staticmethod
    def __emptygen():
        """return an empty generator"""
        if False:
            yield

    def nodes(self, subject: Identifier, predicate: URIRef, obj: Node):
        if subject is not None:
            is_node_iri = self.is_node_iri_in_graph(subject)
            if predicate == RDF.type and obj == VG.Node and is_node_iri:
                yield [(subject, RDF.type, VG.Node), None]
            elif predicate is None and obj == VG.Node and is_node_iri:
                yield [(subject, RDF.type, VG.Node), None]
            elif predicate is None and is_node_iri:
                yield [(subject, RDF.type, VG.Node), None]

            if type(subject) == NodeIriRef:
                yield from self.handle_to_triples(predicate, obj, subject.node_handle())
                yield from self.handle_to_edge_triples(subject, predicate, obj)
            elif is_node_iri:
                subject_iri_parts = subject.toPython().split('/')
                nh = self.odgi_graph.get_handle(int(subject_iri_parts[-1]))
                ns = NodeIriRef(nh,self.base, self.odgi_graph)
                yield from self.handle_to_triples(predicate, obj, nh)
                yield from self.handle_to_edge_triples(ns, predicate, obj)
        else:
            for handle in self.handles():
                ns = NodeIriRef (handle, self.base, self.odgi_graph)
                yield from self.nodes(ns, predicate, obj)

    def is_node_iri_in_graph(self, iri: URIRef):
        if type(iri) == NodeIriRef:
            return True
        else:
            iri_parts = iri.toPython().split('/')
            return 'node' == iri_parts[-2] and self.odgi_graph.has_node(int(iri_parts[-1]))

    def paths(self, subject: Identifier, predicate: URIRef, obj: Node):
        for p in self.knownPaths:
            if subject is None or p == subject:
                # given at RDF.type and the VG.Path as obj we can generate the matching triple
                if (predicate is None or predicate == RDF.type) and (obj is None or obj == VG.Path):
                    yield [(p, RDF.type, VG.Path), None]

    def steps(self, subject: Identifier, predicate: URIRef, obj: Node):

        if subject is None:
            for pathRef in self.knownPaths:
                if not self.odgi_graph.is_empty(pathRef.path()):
                    rank = 1
                    position = 1
                    step_handle = self.odgi_graph.path_begin(pathRef.path())
                    node_handle = self.odgi_graph.get_handle_of_step(step_handle)
                    yield from self.step_handle_to_triples(step_handle, subject, predicate, obj, node_handle=node_handle,
                                                           rank=rank, position=position)

                    while self.odgi_graph.has_next_step(step_handle):
                        step_handle = self.odgi_graph.get_next_step(step_handle)
                        position = position + self.odgi_graph.get_length(node_handle)
                        node_handle = self.odgi_graph.get_handle_of_step(step_handle)
                        rank = rank + 1
                        yield from self.step_handle_to_triples(step_handle, subject, predicate, obj,
                                                               node_handle=node_handle,
                                                               rank=rank, position=position)
        elif type(subject) == StepIriRef:
            yield from self.step_handle_to_triples(subject.step_handle(), subject, predicate, obj, rank=subject.rank(),
                                                   position=subject.position())
        elif type(subject) == StepBeginIriRef:
            yield from self.step_handle_to_triples(subject.step_handle(), subject, predicate, obj, rank=subject.rank(),
                                                   position=subject.position())
        elif type(subject) == StepEndIriRef:
            yield from self.step_handle_to_triples(subject.step_handle(), subject, predicate, obj, rank=subject.rank(),
                                                   position=subject.position())
        else:
            subject_iri_parts = subject.toPython().split('/')
            if 'path' == subject_iri_parts[-4] and 'step' == subject_iri_parts[-2]:
                path_name = subject_iri_parts[-3];
                path_handle = self.odgi_graph.get_path_handle(path_name)
                step_rank = int(subject_iri_parts[-1]);

                if not self.odgi_graph.is_empty(path_handle):
                    rank = 1
                    position = 1
                    step_handle = self.odgi_graph.path_begin(path_handle)
                    node_handle = self.odgi_graph.get_handle_of_step(step_handle)
                    while rank != step_rank and self.odgi_graph.has_next_step(step_handle):
                        rank = rank + 1
                        position = position + self.odgi_graph.get_length(node_handle)
                        step_handle = self.odgi_graph.get_next_step(step_handle)
                        node_handle = self.odgi_graph.get_handle_of_step(step_handle)
                    yield from self.step_handle_to_triples(step_handle, subject, predicate, obj, node_handle=node_handle,
                                                           rank=rank, position=position)

    # else:
    # for nodeHandle in self.handles():
    # for step_handle in self.odgi_graph.steps_of_handle(nodeHandle, False):
    # yield from self.stepHandleToTriples(step_handle, subject, predicate, obj, nodeHandle=nodeHandle)
    def step_handle_to_triples(self,
                               step_handle: odgi.step_handle, subject: Identifier, predicate: URIRef, obj: Node,
                               node_handle: odgi.handle = None, rank=None, position=None):

        if type(subject) == StepIriRef:
            step_iri = subject
        elif type(subject) == StepBeginIriRef:
            step_iri = subject.step_iri()
        elif type(subject) == StepEndIriRef:
            step_iri = subject.step_iri()
        else:
            step_iri = StepIriRef(step_handle, self.base, self.odgi_graph, position, rank)

        if subject is None or step_iri == subject:
            if predicate == RDF.type or predicate is None:
                if obj is None or obj == VG.Step:
                    yield [(step_iri, RDF.type, VG.Step), None]
                if obj is None or obj == FALDO.Region:
                    yield [(step_iri, RDF.type, FALDO.Region), None]
            if node_handle is None:
                node_handle = self.odgi_graph.get_handle_of_step(step_handle)
            node_iri = NodeIriRef(node_handle, self.base, self.odgi_graph)
            if (predicate == VG.node or predicate is None and not self.odgi_graph.get_is_reverse(node_handle)) and (
                    obj is None or node_iri == obj):
                yield [(step_iri, VG.node, node_iri), None]

            if (predicate == VG.reverseOfNode or predicate is None and self.odgi_graph.get_is_reverse(node_handle)) and (
                    obj is None or node_iri == obj):
                yield [(step_iri, VG.reverseOfNode, node_iri), None]

            if (predicate == VG.rank or predicate is None) and rank is not None:
                rank = Literal(rank)
                if obj is None or obj == rank:
                    yield [(step_iri, VG.rank, rank), None]

            if (predicate == VG.position or predicate is None) and position is not None:
                position = Literal(position)
                if obj is None or position == obj:
                    yield [(step_iri, VG.position, position), None]

            if predicate == VG.path or predicate is None:
                path = self.odgi_graph.get_path_handle_of_step(step_handle)
                path_iri = self.find_path_iri_by_handle(path)
                if obj is None or path_iri == obj:
                    yield [(step_iri, VG.path, path_iri), None]

            if predicate is None or predicate == FALDO.begin:
                yield [(step_iri, FALDO.begin, StepBeginIriRef(step_iri)), None]

            if predicate is None or predicate == FALDO.end:
                yield [(step_iri, FALDO.end, StepEndIriRef(step_iri)), None]

            if subject is None:
                begin = StepBeginIriRef(step_iri)
                yield from self.faldo_for_step(step_iri, begin, predicate, obj)
                end = StepEndIriRef(step_iri)
                yield from self.faldo_for_step(step_iri, end, predicate, obj)

        if (type(subject) == StepBeginIriRef) and step_iri == subject.step_iri():
            yield from self.faldo_for_step(subject.step_iri(), subject, predicate, obj)
        elif type(subject) == StepEndIriRef and step_iri == subject.step_iri():
            yield from self.faldo_for_step(subject.step_iri(), subject, predicate, obj)

    def faldo_for_step(self, step_iri: StepIriRef, subject: Identifier, predicate:URIRef, obj: Node):
        ep = Literal(subject.position())
        if (predicate is None or predicate == FALDO.position) and (obj is None or obj == ep):
            yield [(subject, FALDO.position, ep), None]
        if (predicate is None or predicate == RDF.type) and (obj is None or obj == FALDO.ExactPosition):
            yield [(subject, RDF.type, FALDO.ExactPosition), None]
        if (predicate is None or predicate == RDF.type) and (obj is None or obj == FALDO.Position):
            yield [(subject, RDF.type, FALDO.Position), None]
        if predicate is None or predicate == FALDO.reference:
            path = step_iri.path()
            path_iri = self.find_path_iri_by_handle(path)
            if obj is None or obj == path_iri:
                yield [(subject, FALDO.reference, path_iri), None]

    def handle_to_triples(self, predicate, obj, node_handle: odgi.handle):
        node_iri = NodeIriRef(node_handle,self.base, self.odgi_graph)

        if predicate == RDF.value or predicate is None:
            seq_value = rdflib.term.Literal(self.odgi_graph.get_sequence(node_handle))
            if obj is None or obj == seq_value:
                yield [(node_iri, RDF.value, seq_value), None]
        elif (predicate == RDF.type or predicate is None) and (obj is None or obj == VG.Node):
            yield [(node_iri, RDF.type, VG.Node), None]

    def handle_to_edge_triples(self, subject: NodeIriRef, predicate: URIRef, obj: NodeIriRef):
        if predicate is None or (predicate in nodeRelatedPredicates):
            to_node_handles = []
            self.odgi_graph.follow_edges(subject.node_handle(), False, CollectEdges(to_node_handles))
            node_iri = NodeIriRef(subject.node_handle(), self.base,self.odgi_graph)
            for edge in to_node_handles:
                other_iri = NodeIriRef(edge, self.base, self.odgi_graph)
                if obj is None or other_iri == obj:
                    yield from self.generate_edge_triples(edge, subject.node_handle(), node_iri, other_iri, predicate)

    def generate_edge_triples(self, edge, node_handle: odgi.handle, node_iri: NodeIriRef,
                              other_iri: NodeIriRef, predicate: URIRef):
        node_is_reverse = self.odgi_graph.get_is_reverse(node_handle);
        other_is_reverse = self.odgi_graph.get_is_reverse(edge)
        # TODO: check the logic here
        if (
                predicate is None or VG.linksForwardToForward == predicate) and not node_is_reverse and not other_is_reverse:
            yield [(node_iri, VG.linksForwardToForward, other_iri), None]
        if (predicate is None or VG.linksReverseToForward == predicate) and node_is_reverse and not other_is_reverse:
            yield [(node_iri, VG.linksReverseToForward, other_iri), None]
        if (
                predicate is None or VG.linksReverseToReverse == predicate) and node_is_reverse and other_is_reverse:
            yield [(node_iri, VG.linksReverseToReverse, other_iri), None]
        if (
                predicate is None or VG.linksReverseToReverse == predicate) and not node_is_reverse and other_is_reverse:
            yield [(node_iri, VG.linksForwardToReverse, other_iri), None]
        if predicate is None or VG.links == predicate:
            yield [(node_iri, VG.links, other_iri), None]

    def bind(self, prefix, namespace):
        self.namespace_manager.bind(prefix, namespace)

    def namespace(self, search_prefix):
        for prefix, namespace in self.namespace_manager.namespaces():
            if search_prefix == prefix:
                return namespace

    def prefix(self, search_namespace):
        for prefix, namespace in self.namespace_manager.namespaces():
            if search_namespace == namespace:
                return prefix

    def namespaces(self):
        return self.namespace_manager.namespaces()

    def handles(self):
        node_id = self.odgi_graph.min_node_id()

        max_node_id = self.odgi_graph.max_node_id()
        while node_id <= max_node_id:
            if self.odgi_graph.has_node(node_id):
                node_id = node_id + 1
                yield self.odgi_graph.get_handle(node_id - 1)

    def find_path_iri_by_handle(self, path_handle: odgi.path_handle):
        for p in self.knownPaths:
            if p.path() == path_handle:
                return p
            elif self.odgi_graph.get_path_name(p.path()) == self.odgi_graph.get_path_name(path_handle):
                return p
        raise Exception("no path handle known "+str(path_handle))