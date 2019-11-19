import sys

from setuptools import setup

project = "spodgi"
version = "0.0.2"

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name=project,
    version=version,
    description="rdflib extension adding genome graph ODGI back-end store",
    author="Jerven Bolleman",
    author_email="me@jerven.eu",
    url="http://github.com/JervenBolleman/spdogi",
    packages=["spodgi"],
    download_url="https://github.com/JervenBolleman/spodgi/master",
    license="MIT",
    platforms=["any"],
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    python_requires='>=3.6',
    install_requires=[
        "Click>=7.0.0",
        "rdflib>=4.0"
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
