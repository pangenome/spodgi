"""
This module defines the specific IRI objects that are used to avoid joins/refetching by
passing references.

* :class:`Step IRI reference <rdflib.term.URIRef>`
* :class:`Step IRI to end References <rdflib.term.URIRef>`
* :class:`Step IRI to begin References <rdflib.term.URIRef>`
* :class:`Node IRI References <rdflib.term.URIRef>`
"""

from rdflib.term import URIRef
import odgi
from urllib.parse import urlparse

__all__ = [
    'NodeIriRef',
    'StepIriRef',
    'StepEndIriRef',
    'StepBeginIriRef',
    'PathIriRef'
]


class StepIriRef(URIRef):
    __slots__ = ("_stepHandle", "_base", "_odgi", "_position", "_rank")

    def __new__(cls, step_handle: odgi.step_handle, base: str, odgi: odgi, position, rank):
        inst = str.__new__(cls)
        inst._stepHandle = step_handle
        inst._base = base
        inst._odgi = odgi
        inst._rank = rank
        inst._position = position
        return inst

    def __eq__(self, other):

        if StepIriRef == type(other):
            return self._stepHandle == other.step_handle() and self._base == other.base()
        elif isinstance(other, URIRef):
            return URIRef(self.unicode()) == other
        else:
            return False

    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif StepIriRef == type(other):
            if self._base > other.base():
                return True
            elif self._base < other.base():
                return False
            else:
                return self._rank > other.rank()
        elif isinstance(other, URIRef):
            return URIRef(self.unicode()) > other
        else:
            return str(type(self)) > str(type(other))

    def __lt__(self, other):
        return not self.__gt__(other)

    def n3(self, namespace_manager=None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def step_handle(self):
        return self._stepHandle

    def rank(self):
        return self._rank

    def position(self):
        return self._position

    def path(self):
        return self._odgi.get_path_handle_of_step(self.step_handle())

    def odgi(self):
        return self._odgi

    def base(self):
        return self._base

    def toPython(self):
        return self.unicode()

    def unicode(self):
        path_name = self._odgi.get_path_name(self._odgi.get_path_handle_of_step(self._stepHandle))
        try:
            result = urlparse(path_name)
            return f'{path_name}#step-{self._rank}'
        except ValueError:
            return f'{self._base}path/{path_name}/step/{self._rank}'

    def __str__(self):
        return self.unicode()

    def __repr__(self):
        return 'odgi(\'' + self.unicode() + '\')'

    def __hash__(self):
        return hash(self._stepHandle)


class NodeIriRef(URIRef):
    __slots__ = ("_nodeHandle", "_base", "_odgi")

    def __new__(cls, node_handle: odgi.handle, base: str = None, odgi_graph: odgi = None):
        inst = str.__new__(cls)
        inst._nodeHandle = node_handle
        inst._base = base
        inst._odgi = odgi_graph
        return inst

    def __eq__(self, other):
        if type(self) == type(other):
            return self._odgi.get_id(self._nodeHandle) == other.odgi().get_id(
                other.node_handle()) and self._base == other.base()
        elif type(other) == URIRef:
            return URIRef(self.unicode()) == other
        else:
            return False

    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif NodeIriRef == type(other):
            if self._base > other.base():
                return True
            elif self._base < other.base():
                return False
            else:
                return self._odgi.get_id(self._nodeHandle) > self._odgi.get_id(other.node_handle())
        else:
            return type(self) > type(other)

    def n3(self, namespace_manager=None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def toPython(self):
        return self.unicode()

    def unicode(self):
        nid = self._odgi.get_id(self._nodeHandle);
        return f'{self._base}node/{nid}'

    def __str__(self):
        return self.unicode()

    def __repr__(self):
        return 'odgi.NodeIriRef(\'' + self.unicode() + '\')'

    def __hash__(self):
        return self._odgi.get_id(self._nodeHandle)

    def node_handle(self):
        return self._nodeHandle

    def base(self):
        return self._base

    def odgi(self):
        return self._odgi
"""
An IRIRef that keeps a pointer to the step, so that it is quick to extract the
the offset of the step.
"""


class StepBeginIriRef(URIRef):
    __slots__ = "_stepIri"

    def __new__(cls, step_iri: StepIriRef):
        inst = str.__new__(cls)
        inst._stepIri = step_iri
        return inst

    def __eq__(self, other):

        if type(self) == type(other):
            return self._stepIri == other.step_iri();
        elif type(other) == URIRef:
            return URIRef(self.unicode()) == other
        else:
            return False

    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif type(self) == type(other):
            return self._stepIri > other.step_iri()
        else:
            return type(self) > type(other)

    def n3(self, namespace_manager=None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def step_handle(self):
        return self._stepIri.step_handle()

    def step_iri(self):
        return self._stepIri

    def rank(self):
        return self._stepIri.rank()

    def position(self):
        return self._stepIri.position()

    def path(self):
        return self._stepIri.path()

    def toPython(self):
        return self.unicode()

    def unicode(self):
        path_name = self._stepIri.odgi().get_path_name(
            self._stepIri.odgi().get_path_handle_of_step(self.step_handle()))
        try:
            result = urlparse(path_name)
            return f'{path_name}#p{self.position()}'
        except ValueError:
            return f'{self._stepIri.base()}path/{path_name}/position/{self.position()}'

    def __str__(self):
        return self.unicode()

    def __repr__(self):
        return 'odgi.StepBeginIriRef(\'' + self.unicode() + '\')'

    def __hash__(self):
        return hash(self._stepIri)


"""
An IRIRef that keeps a pointer to the step, so that it is quick to extract the
the offset of the step plus the length of the representative node.
"""


class StepEndIriRef(URIRef):
    __slots__ = "_stepIri"

    def __new__(cls, step_iri: StepIriRef):
        inst = str.__new__(cls)
        inst._stepIri = step_iri
        return inst

    def __eq__(self, other):

        if type(self) == type(other):
            return self._stepIri == other.step_iri()
        elif type(other) == URIRef:
            return URIRef(self.unicode()) == other
        else:
            return False

    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif StepEndIriRef == type(other):
            return self._stepIri > other.step_iri()
        elif isinstance(other, URIRef):
            return self.unicode() > other.unicode()
        else:
            return StepEndIriRef > type(other)

    def n3(self, namespace_manager=None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def step_handle(self):
        return self._stepIri.step_handle()

    def step_iri(self):
        return self._stepIri

    def rank(self):
        return self._stepIri.rank()

    def position(self):
        return self._stepIri.position() + self._stepIri.odgi().get_length(
            self._stepIri.odgi().get_handle_of_step(self._stepIri.step_handle()))

    def path(self):
        return self._stepIri.path()

    def toPython(self):
        return self.unicode()

    def unicode(self):
        end = self.position()
        path_name = self._stepIri.odgi().get_path_name(
            self._stepIri.odgi().get_path_handle_of_step(self._stepIri.step_handle()))
        try:
            result = urlparse(path_name)
            return f'{path_name}#p{end}'
        except ValueError:
            return f'{self._stepIri.base()}path/{path_name}/position/{end}'

    def __str__(self):
        return self.unicode()

    def __repr__(self):
        return 'odgi.StepEndIriRef(\'' + self.unicode() + '\')'

    def __hash__(self):
        return hash(self._stepIri)


class PathIriRef(URIRef):
    __slots__ = ("_uri", "_pathHandle")

    def __new__(cls, uri, path_handle: odgi.path_handle):
        inst = str.__new__(cls)
        inst._uri = uri
        inst._pathHandle = path_handle
        return inst

    def __eq__(self, other):

        if type(self) == type(other):
            return self._uri == other.unicode()
        elif type(other) == URIRef:
            return URIRef(self.unicode()) == other
        else:
            return False

    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif type(self) == type(other):
            return self._uri > other.uri
        elif isinstance(other, URIRef):
            return self.unicode() > other.unicode()
        else:
            return PathIriRef > type(other)

    def n3(self, namespace_manager=None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def path(self):
        return self._pathHandle

    def toPython(self):
        return self.unicode()

    def unicode(self):
        return self._uri

    def __str__(self):
        return self.unicode()

    def __repr__(self):
        return 'odgi.PathIriRef(\'' + self.unicode() + '\')'

    def __hash__(self):
        return hash(self._pathHandle)

    def uri(self):
        return self._uri