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

```
./odgi_to_rdf.py ~/git/odgi/test/t.odgi test/t.ttl
```
