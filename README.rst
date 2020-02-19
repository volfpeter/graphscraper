|Downloads|

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

Examples
----------------------

Besides the base graph implementation, the following working examples are also included
in the library, that show you how you can implement and use an actual graph scraper:

- `igraphwrapper`: Instead of web-scraping, this example is using an igraph_ graph
  instance as the "remote" source to scrape data from.
- `spotifyartist`: This example is using the Spotify_ web API to load artists and
  edges are defined by Artist similarity.

Dependencies
-----------------

If you wish to use one of the included graph implementations, then please read the
corresponding module's description for additional requirements.

Contribution
-----------------

Any form of constructive contribution (feedback, features, bug fixes, tests, additional
documentation, etc.) is welcome.

.. _igraph: http://igraph.org
.. _Spotify: https://developer.spotify.com/web-api/
.. |Downloads| image:: https://pepy.tech/badge/graphscraper
