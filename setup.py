#!/usr/bin/env python
import sys

from setuptools import setup

PY2 = sys.version_info.major == 2

project = "rdflib-sqlalchemy"
version = "0.3.8"


setup(
    name=project,
    version=version,
    description="rdflib extension adding genome graph ODGI back-end store",
    author="Jerven Bolleman",
    author_email="me@jerven.eu",
    url="http://github.com/JervenBolleman/spdogi",
    packages=["spodgi"],
    download_url="https://github.com/JervenBolleman/zipball/master",
    license="MIT",
    platforms=["any"],
    long_description="""
    ODGI genome graph store formula-aware implementation.
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    install_requires=[
        "Click>=7.0.0",
        "rdflib>=4.0",
        "six>=1.10.0"
    ],
    setup_requires=[
    
    ],
    tests_require=[
        "pytest"
    ],
    entry_points={
        'rdf.plugins.store': [
            'OdgiStore = spodgi.OdgiStore'
        ]
    }
)
