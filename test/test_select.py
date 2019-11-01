import pytest
import io
from spodgi import OdgiStore

from rdflib.namespace import RDF
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin


def test_open_odgi():
    plugin.register('OdgiStore', Store,'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    count=0;
    for t in spodgi.triples((None, None, None)):
        (s, p, o) = t
        assert s != None
        assert p != None
        assert o != None
        count=count+1
    assert count > 40
    spodgi.close()

def test_count_all():
    assert True
