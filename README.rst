GraphScraper
=================

GraphScraper is a Python 3 library that contains a base graph implementation designed
to be turned into a web scraper for graph data. It has two major features:
1) The graph automatically manages a database (using either SQLAlchemy or
   Flask-SQLAlchemy) where it stores all the nodes and edges the graph has seen.
2) The base graph implementation provides hook methods that, if implemented,
   turn the graph into a web scraper.

Demo - igraph
------------------

Besides the actual graph implementation, a working demo using the igraph_ library
is also included that shows how you can implement and use an actual graph-scraper.
Instead of actual web-scraping, this demo uses igraph graph instance as the "remote"
source to scrape data from.

Dependencies
-----------------

The project requires SQLAlchemy_ or Flask-SQLAlchemy_ to be installed.
If you wish to the included igraph-based graph implementation, you will also need
igraph_ library.

Contribution
-----------------

Any form of constructive contribution (feedback, features, bug fixes, tests, additional
documentation, etc.) is welcome.

.. _Flask-SQLAlchemy: http://flask-sqlalchemy.pocoo.org/
.. _igraph: http://igraph.org
.. _SQLAlchemy: https://www.sqlalchemy.org/
