"""
The root package of the graphscraper project.
"""

# Imports
# ------------------------------------------------------------

# Expose the core modules for ease of use.
from . import base
from . import db

# No need to expose the eventdispatcher module. It won't be needed by the user.
# from . import eventdispatcher

# Do not import the rest of the modules, because they have dependencies that
# might not be available on the user's machine.
# from . import demo
# from . import igraphwrapper

# Module constants
# ------------------------------------------------------------

__author__ = 'Peter Volf'
