# SpOdgi
Use a general graph query language SPARQL to investigate genome variation graphs!

Currently it exposes any [Odgi](https://github.com/vgteam/odgi) genome variation graph via SPARQL a W3C standard query language. At the moment this is read only mode, and one can not modify the graph using SPARQL update yet.

# Help wanted

This is a hobby for me, but could be very useful for others so please join and hack on this ;)

I am especially in need of current best practices for packaging and testing of code in python. There is a `setup.py` but it is rough and probably needs a lot of work.

# How to run

You need to have Odgi build locally and added it's pybind module directory to your PYTHONPATH. If you work like me it would be checked out in `~/git/odgi` and then you can use the env.sh script

You need to have an Odgi file. So conversion from GFA
needs to be done using `odgi build -g test/t.gfa -o test/o.odgi`

# Running a SPARQL query on a Odgi

```bash
./sparql_odgi.py  test/t.odgi 'ASK {<http://example.org/node/1> a <http://biohackathon.org/resource/vg#Node>}'
```

Finding the nodes with sequences that are longer than 5 nucleotides

```bash
./sparql_odgi.py  test/t.odgi 'PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> SELECT ?seq WHERE {?x rdf:value ?seq . FILTER(strlen(?seq) >5)}'

```
See more example queries in the queries directory. You can run them like this.

```bash
./sparql_odgi.py test/t.odgi "$(cat queries/selectAllSteps.rq)"
```

# Variation Graphs as RDF/semantic graphs.

The modelling is following what is described in the [vg](/vgteam/vg) repository. 
Such as in the [ontology directory](/vgteam/vg/tree/master/ontology)

# Converting an Odgi into RDF

The code should support all RDF serialisations supported by RDFLib.

```bash
./odgi_to_rdf.py --syntax=ttl test/t.odgi test/t.ttl
```
This makes the same kind of turtle as done by the `vg view -t` code.
However, it adds more `rdf:type` statements as well as makes it easier to map from a linear genome because each step is also a region on the linear genome encoded using `faldo:Region` as it  would be in the Ensembl or UniProt RDF.

# How can this work?

## Mapping between types/predicates and known objects

The trick is that in VG RDF there are almost one to one mappings between a `rdf:type` or a predicate and a handlgegraph object type. For example if we see `vg:Node` we know we are dealing with a `handle`, if we see `rdf:value` as predicate we know it works on the node sequences. All VG and FALDO predicates, classes and literals map straight forwards to a known set of Odgi/libhandlegraph methods and objects.

| Predicate | Object/Class |
| `rdf:value` | Node->sequence |
| `vg:links` | Node->Node (Edge) |
| `vg:linksReverseToReverse` | Node->Node (Edge) |
| `vg:linksReverseToForward` | Node->Node (Edge) |
| `vg:linksForwardToReverse` | Node->Node (Edge) |
| `vg:linksForwardToForward` | Node->Node (Edge) |
| `vg:reverseOfNode` | Step->Node |
| `vg:node` | Step->Node |
| `vg:path` | Step->Path |
| `vg:rank` | Step->count allong it's Path |
| `vg:offset` | Step->count allong it's Path |
| `faldo:begin` | Step->position |
| `faldo:end` | Step->position + Node->sequence.length|
| `faldo:reference` | Step->Path |
| `rdf:label` | Path->name |

|Types | Object/Class |
| `vg:Node` | `Node` |
| `vg:Step` | `Step` |
| `faldo:Region` | `Step` |
| `vg:Path` | `Path` |
| `faldo:ExactPosition` | Step->begin/end (all are known exactly) |
| `faldo:Position` | Step->begin/end (all are known exactly, but allows easier querying) |

## SPARQL engines need one method to override

The way the SPARQL engines are build allows us to get the full (if not optimal) solutions by just implementating a single method. In the RDFLib case this is called `triples` which accepts a triple pattern and a `Context` (Named graph).

For each triple pattern we generate all possible matching triples using python generators (`yield`). For example if we see in triple pattern with `rdf:type` as predicate we know we need to iterate over all Odgi objects and return for each of them the triples where the `rdf:type` is set. If the predicate is not known we return an empty generator.



# How to run

Currently this needs a specific branch of Odgi for more python support (specifically equals methods on step objects).
Once that is installed and build you can look into the [env.sh](/spodgi/blob/master/env.sh), to make sure the Odgi pythonmodule is on your path.

Then you can use the setup.py to install SpOdgi.

# Notes

## Methods in Odgi

The code to access Odgi methods/objects is listed in [Odgi src pythonmodule.cpp](https://github.com/vgteam/odgi/blob/master/src/pythonmodule.cpp)

## RDFLib 4.x

## Python3 Generators

## Avoiding fetching known data

To avoid needing to re-fetch data we already fetched from disk/Odgi multiple times for a simple join we attach the reference to the Odgi object to the associated RDFLib URIRef objects.
We do this by extending URIRef with our own implementations in [](/spodgi/blob/master/spodgi/terms.py).
This is useful because the lazy manner of generator use in the RDFLib query engine leads to normal reasonable queries encouraging Odgi objects to have a short live time.

This is also made possible because we use predictable patterns in our IRIs. For example we encode the path/step_rank/position for the `faldo:Position` objects in their IRIs. This means that given an IRI like this we can use the Odgi (or other libhandlegraph) indexes for efficient access.

## Odgi does not have an index for Rank/Position of Steps

This means we need to use an iterator from 0 for every step access. We can be no faster than Odgi here.
Unfortunately a lot of interesting queries for visualisation are very much driven by a natural linearisation of the genome variation graph.
