import pytest
import io
from spodgi import OdgiStore

from rdflib.namespace import RDF
from rdflib.store import Store
from rdflib import Graph
from rdflib import plugin
from rdflib.collection import Collection


def test_open_odgi():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    count = 0;
    for t in spodgi.triples((None, None, None)):
        (s, p, o) = t
        assert s is not None
        assert p is not None
        assert o is not None
        count = count + 1
    assert count > 40
    spodgi.close()


def test_count_all():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    for r in spodgi.query('SELECT (count(*) as ?count) WHERE {?s ?p ?o}'):
        assert r[0].value > 195

    spodgi.close()
    assert True


def test_count_all_distinct():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    for r in spodgi.query('SELECT (count(distinct *) as ?count) WHERE {?s ?p ?o}'):
        assert r[0].value == 195

    spodgi.close()
    assert True


def test_count_distinct_subject():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    for r in spodgi.query('SELECT (count(distinct ?s) as ?count) WHERE {?s ?p ?o}'):
        assert r[0].value == 37

    spodgi.close()
    assert True


def test_count_distinct_steps():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    for r in spodgi.query('''PREFIX vg:<http://biohackathon.org/resource/vg#>
    SELECT (count(distinct ?s) as ?count) WHERE {?s a vg:Step}'''):
        assert r[0].value == 10

    spodgi.close()
    assert True


def test_count_distinct_object():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)

    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                          SELECT (count(distinct ?o) as ?count) WHERE {?s faldo:reference ?o}'''):
        assert r[0].value == 1
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                          SELECT (count(distinct ?o) as ?count) WHERE {?s faldo:begin ?o}'''):
            assert r[0].value == 10
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                              SELECT (count(distinct ?o) as ?count) WHERE {?s faldo:end ?o}'''):
        assert r[0].value == 10
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT (count(distinct ?o) as ?count) WHERE {?s vg:rank ?o}'''):
        assert r[0].value == 10
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT (count(distinct ?o) as ?count) WHERE {?s vg:node ?o}'''):
        assert r[0].value == 10
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT (count(distinct ?o) as ?count) WHERE {?s vg:node ?o}'''):
        assert r[0].value == 10
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT (count(distinct ?o) as ?count) WHERE {?s vg:links ?o}'''):
        assert r[0].value == 14
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT (count(distinct ?o) as ?count) WHERE {?s vg:linksForwardToForward ?o}'''):
        assert r[0].value == 14
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT (count(distinct ?o) as ?count) WHERE {?s faldo:position ?o}'''):
        assert r[0].value == 11
    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT distinct ?s 
                        WHERE {{?s a faldo:Position }UNION {?s a faldo:ExactPosition }}'''):
        print(r[0], type(r[0]))

    for r in spodgi.query('''PREFIX faldo:<http://biohackathon.org/resource/faldo#>
                        PREFIX vg:<http://biohackathon.org/resource/vg#>
                        SELECT (count(distinct ?s) as ?count) 
                        WHERE {{?s a faldo:Position }UNION {?s a faldo:ExactPosition }}'''):
        assert r[0].value == 11
    # for r in spodgi.query('SELECT ?p (count(distinct ?o) as ?count) WHERE {?s ?p ?o} GROUP BY ?p'):
    #     print(r[0], ':', r[1])


    spodgi.close()
    assert True


def test_count_distinct_referenced_node():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    for r in spodgi.query('''PREFIX vg:<http://biohackathon.org/resource/vg#>
SELECT (count(distinct ?s) as ?count) WHERE {?s a vg:Node}'''):
        assert r[0].value == 15
    for r in spodgi.query('''PREFIX vg:<http://biohackathon.org/resource/vg#>
SELECT (count(distinct ?n) as ?count) WHERE {?s vg:node ?n}'''):
        assert r[0].value == 10 # See P line in odgi/test/t.gfa

    spodgi.close()
    assert True


def test_select_specific_step():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    for r in spodgi.query('SELECT ?rank WHERE {<path/x/step/2> <http://biohackathon.org/resource/VG#rank> ?rank}'):
        assert r[0].value == 2

    spodgi.close()
    assert True


def test_select_specific_sequence():
    plugin.register('OdgiStore', Store, 'spodgi.OdgiStore', 'OdgiStore')
    s = plugin.get('OdgiStore', Store)(base="http://example.org/test/")
    spodgi = Graph(store=s)
    spodgi.open('./test/t.odgi', create=False)
    for r in spodgi.query('SELECT ?sequence WHERE {<node/2> rdf:value ?sequence}'):
        assert r[0].value == 'A'

    spodgi.close()
    assert True
