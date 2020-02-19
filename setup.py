from codecs import open
from os import path
from setuptools import setup, find_packages

# Get the long description from the README file
with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="graphscraper",
    version="0.5.0",
    description="Graph implementation that loads graph data (nodes and edges) from external sources "
                "and caches the loaded data in a database using sqlalchemy or flask-sqlalchemy.",
    long_description=long_description,
    url="https://github.com/volfpeter/graphscraper",
    author="Peter Volf",
    author_email="do.volfp@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Topic :: Database",
        "Topic :: Internet",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities"
    ],
    keywords="graph network webscraping sqlalchemy database db caching",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3",
    install_requires=["sqlalchemy>=1.3"]
)
