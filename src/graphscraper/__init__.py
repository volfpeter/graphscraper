"""
The root package of the graphscraper project.
"""

# Imports
# ------------------------------------------------------------

# Expose the core modules for ease of use.
from graphscraper import base
from graphscraper import db

# No need to expose the eventdispatcher module. It won't be needed by the user.
# from graphscraper import eventdispatcher

# Do not import the rest of the modules, because they have dependencies that
# might not be available on the user's machine.
# from graphscraper import demo
# from graphscraper import igraphwrapper

# Module constants
# ------------------------------------------------------------

__author__ = 'Peter Volf'
