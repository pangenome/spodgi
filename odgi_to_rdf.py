#!/usr/bin/python3
import odgi
import rdflib
import click
import io

class ToTurtle:
    def __init__(self, og):
        self.og = og
    def __call__(self, handle):
        print(self.og.get_id(handle))
        print(self.og.get_sequence(handle))


@click.command()
@click.argument('odgifile')
@click.argument('ttl', type=click.File('wb'))
def main(odgifile, ttl):
    og = odgi.graph()
    ogf = og.load(odgifile)
    ogo = og.optimize(ogf)
    og.for_each_handle(ToTurtle(og))
    

if __name__ == "__main__":
    main()

