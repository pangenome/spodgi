"""
This module defines the specific IRI objects that are used to avoid joins/refetching by
passing references.

* :class:`Step IRI reference <rdflib.term.URIRef>`
* :class:`Step IRI to end References <rdflib.term.URIRef>`
* :class:`Step IRI to begin References <rdflib.term.URIRef>`
* :class:`Node IRI References <rdflib.term.URIRef>`
"""

import odgi
from rdflib.term import URIRef

__all__ = [
    'NodeIriRef',
    'StepIriRef',
    'StepIriEndRef',
    'StepIriBeginRef',
]

class StepIriRef(URIRef):
    __slots__ = ("_stepHandle", "_base", "_odgi", "_position", "_rank")
    
    def __new__(cls, stepHandle, base, odgi, position, rank):
         inst =  str.__new__(cls)
         inst._stepHandle = stepHandle
         inst._base = base
         inst._odgi = odgi
         inst._rank = rank
         inst._position = position
         return inst
      
    def __eq__(self, other):
        
        if type(self) == type(other):
            return self._stepHandle == other._stepHandle and self._base == other._base
        elif (type(other) == URIRef):
            return URIRef(self.unicode()) == other
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
            
    def __lt__(self, other):
        return not self.__gt(other)
            
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
        return self._odgi.get_path_handle_of_step(self.stepHandle())
        
    def toPython(self):
        return self.unicode()
        
    def unicode(self):
        return f'{self._base}path/{self._odgi.get_path_name(self._odgi.get_path_handle_of_step(self._stepHandle))}/step/{self._rank}'
    
    def __str__(self):
        return self.unicode()
    
    def __repr__(self):
        return 'odgi.StepIriRef(\''+self.unicode()+'\')'

    def __hash__(self):
        return hash(self._stepHandle)

class NodeIriRef(URIRef):
    __slots__ = ("_nodeHandle", "_base", "_odgi")
    
    def __new__(cls, nodeHandle, base, odgi):
         inst =  str.__new__(cls)
         inst._nodeHandle = nodeHandle
         inst._base = base
         inst._odgi = odgi
         return inst
      
    def __eq__(self, other):
        if type(self) == type(other):
            return self._odgi.get_id(self._nodeHandle) == self._odgi.get_id(other._nodeHandle) and self._base == other._base
        elif (type(other) == URIRef):
            return URIRef(self.unicode()) == other
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
    
    def __str__(self):
        return self.unicode()
    
    def __repr__(self):
        return 'odgi.NodeIriRef(\''+self.unicode()+'\')'

    def __hash__(self):
        return self._odgi.get_id(self._nodeHandle)

"""
An IRIRef that keeps a pointer to the step, so that it is quick to extract the
the offset of the step.
"""
class StepBeginIriRef(URIRef):
    __slots__ = ("_stepIri")
    
    def __new__(cls, stepIri):
         inst =  str.__new__(cls)
         inst._stepIri = stepIri
         return inst
      
    def __eq__(self, other):
        
        if type(self) == type(other):
            return self._stepIri == other._stepIri
        elif (type(other) == URIRef):
            return URIRef(self.unicode()) == other
        else:
            return False
                
    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif type(self) == type(other):
            return self._stepIri > other._stepIri
            
    def n3(self, namespace_manager = None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def stepHandle(self):
        return self._stepIri._stepHandle
    
    def rank(self):
        return self._stepIri._rank
    
    def position(self):
        return self._stepIri._position
    
    def path(self):
        return self._stepIri.path()
        
    def toPython(self):
        return self.unicode()
        
    def unicode(self):
        return f'{self._stepIri._base}path/{self._stepIri._odgi.get_path_name(self._stepIri._odgi.get_path_handle_of_step(self._stepIri._stepHandle))}/step/{self._stepIri._rank}/begin/{self._stepIri._position}'
    
    def __str__(self):
        return self.unicode()
    
    def __repr__(self):
        return 'odgi.StepIriBeginRef(\''+self.unicode()+'\')'

    def __hash__(self):
        return hash(self._stepIri)

"""
An IRIRef that keeps a pointer to the step, so that it is quick to extract the
the offset of the step plus the length of the representative node.
"""
class StepEndIriRef(URIRef):
    __slots__ = ("_stepIri")
    
    def __new__(cls, stepIri):
         inst =  str.__new__(cls)
         inst._stepIri = stepIri
         return inst
      
    def __eq__(self, other):
        
        if type(self) == type(other):
            return self._stepIri == other._stepIri
        elif (type(other) == URIRef):
            return URIRef(self.unicode()) == other
        else:
            return False
                
    def __gt__(self, other):
        if other is None:
            return True  # everything bigger than None
        elif type(self) == type(other):
            return self._stepIri > other._stepIri
            
    def n3(self, namespace_manager = None):
        if namespace_manager:
            return namespace_manager.normalizeUri(self)
        else:
            return f'<{self.unicode()}>'

    def stepHandle(self):
        return self._stepIri._stepHandle
    
    def rank(self):
        return self._stepIri._rank
    
    def position(self):
        return self._stepIri._position + self._stepIri._odgi.get_length(self._stepIri._odgi.get_handle_of_step(self._stepIri._stepHandle))
    
    def path(self):
        return self._stepIri.path()
        
    def toPython(self):
        return self.unicode()
        
    def unicode(self):
        end = self.position()
        return f'{self._stepIri._base}path/{self._stepIri._odgi.get_path_name(self._stepIri._odgi.get_path_handle_of_step(self._stepIri._stepHandle))}/step/{self._stepIri._rank}/end/{end}'
    
    def __str__(self):
        return self.unicode()
    
    def __repr__(self):
        return 'odgi.StepIriEndRef(\''+self.unicode()+'\')'

    def __hash__(self):
        return hash(self._stepIri)
