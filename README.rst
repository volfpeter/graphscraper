GraphScraper
=================

GraphScraper is a Python 3 library that contains a base graph implementation designed
to be turned into a web scraper for graph data. It has two major features:

1) The graph automatically manages a database (using either SQLAlchemy or
Flask-SQLAlchemy) where it stores all the nodes and edges the graph has seen.

2) The base graph implementation provides hook methods that, if implemented,
turn the graph into a web scraper.

Yet another graph implementation - why
-------------------------------------------

There are many excellent graph libraries available for different purposes. I started
implementing this one because i haven't found a graph library that is dynamic (i don't
need the whole graph in memory - or on disk - before i start working with it), that
can be used as a web scraper (to seamlessly load nodes and edges from some remote
data source when that piece of data is needed) and that keeps all data (the graph)
automatically up-to-date on the disk. GraphScraper aims to satisfy these requirements.

Demo - igraph
------------------

Besides the base graph implementation, a working demo using the igraph_ library
is also included that shows how you can implement and use an actual graph-scraper.
Instead of web-scraping, this demo uses an igraph graph instance as the "remote"
source to scrape data from.

Dependencies
-----------------

The project requires SQLAlchemy_ or Flask-SQLAlchemy_ to be installed.
If you wish to use the included igraph-based graph implementation, you will also
need the igraph_ library.

Contribution
-----------------

Any form of constructive contribution (feedback, features, bug fixes, tests, additional
documentation, etc.) is welcome.

.. _Flask-SQLAlchemy: http://flask-sqlalchemy.pocoo.org/
.. _igraph: http://igraph.org
.. _SQLAlchemy: https://www.sqlalchemy.org/
