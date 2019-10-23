# spodgi
RDF and SPARQL ideas to build on top of [vgteam/odgi](https://github.com/vgteam/odgi)

# Example

You need to have odgi build and added it's pybind module directory to your PYTHONPATH.
If you work like me it would be checked out in `~/git/odgi` and then you can use the env.sh script

I currently depend on two pip installs 
* [Click](https://click.palletsprojects.com/en/7.x/)
* [rdflib](https://rdflib.readthedocs.io/en/stable/)

You need to have an odgi file. So conversion from GFA
needs to be done using `odgi build -g test/t.gfa -o test/o.odgi`

# Conversion to turtle
```
./odgi_to_rdf.py ~/git/odgi/test/t.odgi test/t.ttl
```

# Running a SPARQL query on a ODGI

```bash
./sparql_odgi.py  ../odgi/test/t.odgi 'ASK {<http://example.org/node/1> a <http://biohackathon.org/resource/vg#Node>}'
```

Finding the nodes with sequences that are longer than 5 nucleotides

```bash
./sparql_odgi.py  ../odgi/test/t.odgi 'PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> SELECT ?seq WHERE {?x rdf:value ?seq . FILTER(strlen(?seq) >5)}'

```

# Ideas

Write out the data from an `odgi` file to rdf. For now `turtle` but pragmatically anything supported by RDFlib. 

The end state is to translate SPARQL queries directly via the RDFLib engine to odgi graph calls. Which would make any odgi file available on the semantic web. Making any `handlegraph` system a SPARQL endpoint if so desired.

# Help wanted

This is a hobby for me, but could be very useful for others so please join and hack on this ;)

# Methods in ODGI

The code to map to ODGI is listed in [ODGI src pythonmodule.cpp](https://github.com/vgteam/odgi/blob/master/src/pythonmodule.cpp)

# How can this work?

The trick is that in VG RDF there are almost one to one mappings between a `rdf:type` or a predicate and a handlgegraph object type. For example if we see `vg:Node` we know we are dealing with a `handle`, if we see `rdf:value` as predicate the same. These predicates, classes and objects map straight forward.
