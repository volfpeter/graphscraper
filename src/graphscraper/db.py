"""
Database interface definition for the graph implementation.
"""

# Imports
# ------------------------------------------------------------

from typing import List, Optional

import datetime

try:
    from sqlalchemy.engine.base import Engine
    from sqlalchemy.ext.declarative.api import DeclarativeMeta
    from sqlalchemy.orm import RelationshipProperty
    from sqlalchemy.orm.session import Session
except ImportError:
    # SQLAlchemy imports failed (they are used for typing only, so no problem).
    Engine = None
    DeclarativeMeta = None
    RelationshipProperty = None
    Session = None

# Module constants
# ------------------------------------------------------------

__author__ = "Peter Volf"

# Classes
# ------------------------------------------------------------


class DBNode(object):
    """
    Interface specification for the node database object model.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, node_name: str, external_id: str = None):
        """
        Initialization.

        Arguments:
            node_name (str): The name of the node.
            external_id (str): The external ID of the node.
        """
        # We must not only declare the properties but also initialize them,
        # otherwise the IDE will show warnings wherever the properties are accessed.

        self.are_neighbors_cached: bool = False
        """Whether the neighbors of the node have already been added to the database."""

        self.edges_where_source: List["DBEdge"] = []
        """The list of edges in the database where this node is the source."""

        self.edges_where_target: List["DBEdge"] = []
        """The list of edges in the database where this node is the target."""

        self.name: str = node_name
        """The name of the node."""

        self.external_id: Optional[str] = external_id.strip() if external_id is not None else None
        """The external ID of the node."""

        raise NotImplementedError("DBNode is just an abstract base class that defines the "
                                  "interface of actual node model objects. {}".format(node_name))

    # Properties
    # ------------------------------------------------------------

    @property
    def creation_date(self) -> datetime.date:
        """
        The date when the node was created.
        """
        raise NotImplementedError("DBNode is just an abstract base class that defines "
                                  "the interface of actual node model objects.")

    @property
    def edges(self) -> List["DBEdge"]:
        """
        The edges where this node is one of the endpoints.
        """
        raise NotImplementedError("DBNode is just an abstract base class that defines "
                                  "the interface of actual node model objects.")

    @property
    def neighbor_names(self) -> List[str]:
        """
        The names of the neighbors of the node that are currently in the database.
        """
        raise NotImplementedError("DBNode is just an abstract base class that defines "
                                  "the interface of actual node model objects.")

    @property
    def neighbors(self) -> List["DBNode"]:
        """
        The list of neighbors the node currently has in the database.
        """
        raise NotImplementedError("DBNode is just an abstract base class that defines "
                                  "the interface of actual node model objects.")

    # Class methods
    # ------------------------------------------------------------

    @classmethod
    def find_by_name(cls, node_name: str) -> Optional["DBNode"]:
        """
        Returns the `DBNode` with the given name if such a node exists in the database.

        Arguments:
            node_name (str): The queried node name.

        Returns:
            The node with the given name if it exists.
        """
        raise NotImplementedError("DBNode is just an abstract base class that defines "
                                  "the interface of actual node model objects.")

    @classmethod
    def find_by_external_id(cls, external_id: str) -> Optional["DBNode"]:
        """
        Returns the `DBNode` with the given external ID if such a node exists in the database.

        Arguments:
            external_id (str): The queried external ID.

        Returns:
            The node with the given external ID if it exists.
        """
        raise NotImplementedError("DBNode is just an abstract base class that defines "
                                  "the interface of actual node model objects.")


class DBEdge(object):
    """
    Interface specification for the edge database object model.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, source_name: str, target_name: str, weight: float = 1):
        """
        Initialization.

        Arguments:
            source_name (str): The name of the source node of the edge.
            target_name (str): The name of the target node of the edge.
            weight (float): The weight of the edge.
        """
        # We must not only declare the properties but also initialize them,
        # otherwise the IDE will show warnings wherever the properties are accessed.

        self.source_name: str = source_name
        """The name of the source node of the edge."""

        self.target_name: str = target_name
        """The name of the target node of the edge."""

        self.weight: float = weight
        """The weight of the edge."""

        raise NotImplementedError("DBEdge is just an abstract base class that defines "
                                  "the interface of actual edge model objects. "
                                  "{} - {} ({})".format(source_name, target_name, weight))

    # Class methods
    # ------------------------------------------------------------

    @classmethod
    def find_by_name(cls, source_name: str, target_name: str) -> Optional["DBEdge"]:
        """
        Returns the `DBEdge` connecting the edges with the given names if such an edge
        currently exists in the database.

        Arguments:
            source_name (str): The name of one of the endpoints of the queried edge.
            target_name (str): The name of the other endpoint of the queried edge.

        Returns:
            The edge connecting the given nodes in the database if such an edge exists.
        """
        raise NotImplementedError("DBEdge is just an abstract base class that defines "
                                  "the interface of actual edge model objects.")


class GraphDatabaseInterface(object):
    """
    Database interface implementation that provides users access to a graph database model
    using SQLAlchemy or Flask-SQLAlchemy.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self,
                 session: Session,
                 node: DBNode,
                 edge: DeclarativeMeta):
        """
        Initialization.
        """
        self.session: Session = session
        """The session used to execute database operations."""

        self.Node: DBNode = node
        """The database object model metaclass for nodes."""
        self.set_query_on_table_metaclass(self.Node, self.session)

        self.Edge: DBEdge = edge
        """The database object model metaclass for edges."""
        self.set_query_on_table_metaclass(self.Edge, self.session)

    # Static methods
    # ------------------------------------------------------------

    @staticmethod
    def set_query_on_table_metaclass(model: object, session: Session):
        """
        Ensures that the given database model (`DeclarativeMeta`) has a `query` property through
        which the user can easily query the corresponding database table.

        Database object models derived from Flask-SQLAlchemy's `database.Model` have this property
        set up by default, but when using SQLAlchemy, this may not be the case. In this method this
        problem we fix.

        Argumentss:
            model (DeclarativeMeta): The database model object whose `query` property should be
                                     set up if it's not set up already.
            session (Session): The session to use to set up the `query` property on `model`.
        """
        if not hasattr(model, "query"):
            model.query = session.query(model)

# Methods
# ------------------------------------------------------------


def create_graph_database_interface(db: Engine,
                                    session: Session,
                                    declarative_meta: DeclarativeMeta,
                                    relationship: RelationshipProperty) -> GraphDatabaseInterface:
    """
    Creates a graph database interface to the database specified by the input arguments.

    Note that the created database model assumes that the database enforces constraints such
    as foreign key validity. This is _not true_ for SQLite databases for example, where
    `PRAGMA foreign_key` is off by default. If you don't ensure that the database enforces
    constraints, then some of the database tables might end up containing invalid records.

    SQLAlchemy example:
        >>> try:
        >>>     import sqlalchemy
        >>>     from sqlalchemy.ext.declarative import declarative_base
        >>>     from sqlalchemy.orm import sessionmaker
        >>> except ImportError:
        >>>     raise ImportError("SQLAlchemy not found.")
        >>>
        >>> # Import this method
        >>> # import create_graph_database_interface
        >>>
        >>> # Database interface setup.
        >>> Base = declarative_base()
        >>> engine = sqlalchemy.create_engine("sqlite://")
        >>> Session = sessionmaker(bind=engine)
        >>> dbi: GraphDatabaseInterface = create_graph_database_interface(
        >>>     sqlalchemy,
        >>>     Session(),
        >>>     Base,
        >>>     sqlalchemy.orm.relationship
        >>> )
        >>>
        >>> # Complete database reset.
        >>> Base.metadata.drop_all(engine)
        >>> Base.metadata.create_all(engine)
        >>>
        >>> # Database interface test.
        >>> node: DBNode = dbi.Node("Some vertex")
        >>> dbi.session.add(node)
        >>> dbi.session.commit()
        >>>
        >>> node = dbi.Node.find_by_name("Some vertex")
        >>> if node is not None:
        >>>     print("Got it!")

    Flask-SQLAlchemy example:
        >>> try:
        >>>     from flask import Flask
        >>>     from flask_sqlalchemy import SQLAlchemy
        >>> except ImportError:
        >>>     raise ImportError("The flask and flask-sqlalchemy libraries are required in this example.")
        >>>
        >>> # Import this method
        >>> # import create_graph_database_interface
        >>>
        >>> # Set up the Flask application.
        >>> app = Flask(__name__)
        >>> app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        >>> flask_db = SQLAlchemy(app)
        >>>
        >>> # Create the database interface
        >>> dbi: GraphDatabaseInterface = create_graph_database_interface(
        >>>     flask_db,
        >>>     flask_db.session,
        >>>     flask_db.Model,
        >>>     flask_db.relationship
        >>> )
        >>>
        >>> # Complete database reset.
        >>> flask_db.drop_all()
        >>> flask_db.create_all()
        >>>
        >>> # Database interface test.
        >>> node: DBNode = dbi.Node("Some vertex")
        >>> dbi.session.add(node)
        >>> dbi.session.commit()
        >>>
        >>> node = dbi.Node.find_by_name("Some vertex")
        >>> if node is not None:
        >>>     print("Got it!")

    Arguments:
        db (Engine): The SQLAlchemy or Flask-SQLAlchemy database to use.
        session (Session): The session database operations are executed on.
        declarative_meta (DeclarativeMeta): The metaclass that should be the base class
                                            of the database model classes.
        relationship (RelationshipProperty): Relationship property generator.

    Returns:
        A graph database interface object the user can use to query and manipulate the database
        that is specified by the input arguments of the method.
    """

    class DBNode(declarative_meta):
        """
        Declarative database object model representing a node.
        """

        # Metaclass definition
        # ------------------------------------------------------------

        # __bind_key__ = bind_key  # Variable name must not be changed.
        __tablename__ = "nodes"  # Variable name must not be changed.

        _creation_date = db.Column(db.Date,
                                   nullable=False,
                                   default=datetime.date.today)

        are_neighbors_cached = db.Column(db.Boolean,
                                         default=False)
        name = db.Column(db.String(100),
                         primary_key=True)
        external_id = db.Column(db.String(100))

        edges_where_source = relationship("DBEdge",
                                          primaryjoin="DBNode.name==DBEdge.source_name",
                                          cascade="all, delete-orphan",
                                          backref="source")
        edges_where_target = relationship("DBEdge",
                                          primaryjoin="DBNode.name==DBEdge.target_name",
                                          cascade="all, delete-orphan",
                                          backref="target")

        # Initialization
        # ------------------------------------------------------------

        def __init__(self, node_name: str, external_id: str = None):
            """
            Initialization.

            Arguments:
                node_name (str): The name of the node.
                external_id (str): The external ID of the node.
            """
            if node_name is None:
                raise ValueError("Node name must not be None.")

            node_name = node_name.strip()
            if len(node_name) == 0:
                raise ValueError("Node name must contain non-whitespace characters.")

            self.name = node_name
            self.external_id = external_id.strip() if external_id is not None else None

        # Special methods
        # ------------------------------------------------------------

        def __repr__(self) -> str:
            """
            The string representation of the object.
            """
            return "DBNode(name={}, external_id={})".format(self.name, self.external_id)

        # Properties
        # ------------------------------------------------------------

        @property
        def creation_date(self) -> datetime.date:
            """
            The date when the node was created.
            """
            return self._creation_date

        @property
        def edges(self) -> List["DBEdge"]:
            """
            The edges where this node is one of the endpoints.
            """
            result: List["DBEdge"] = []
            edges: List["DBEdge"] = self.edges_where_target
            if edges is not None:
                result.extend(edges)

            edges = self.edges_where_source
            if edges is not None:
                result.extend(edges)

            return result

        @property
        def neighbor_names(self) -> List[str]:
            """
            The names of the neighbors of the node that are currently in the database.
            """
            result: List[str] = []
            neighbors: List[str] = [edge.source_name
                                    for edge in DBEdge.query.filter_by(target_name=self.name)]
            if neighbors is not None:
                result.extend(neighbors)

            neighbors = [edge.target_name
                         for edge in DBEdge.query.filter_by(source_name=self.name)]
            if neighbors:
                result.extend(neighbors)

            return result

        @property
        def neighbors(self) -> List["DBNode"]:
            """
            The list of neighbors the node currently has in the database.
            """
            result: List[DBNode] = []

            neighbors: List[DBNode] = [edge.source for edge in DBEdge.query.filter_by(target_name=self.name)]
            if neighbors is not None:
                result.extend(neighbors)

            neighbors = [edge.target for edge in DBEdge.query.filter_by(source_name=self.name)]
            if neighbors is not None:
                result.extend(neighbors)

            return result

        # Class methods
        # ------------------------------------------------------------

        @classmethod
        def find_by_name(cls, node_name: str) -> Optional["DBNode"]:
            """
            Returns the `DBNode` with the given name if such a node exists in the database.

            Arguments:
                node_name (str): The queried node name.

            Returns:
                The node with the given name if it exists.
            """
            return cls.query.filter_by(name=node_name).first()

        @classmethod
        def find_by_external_id(cls, external_id: str) -> Optional["DBNode"]:
            """
            Returns the `DBNode` with the given external ID if such a node exists in the database.

            Arguments:
                external_id (str): The queried external ID.

            Returns:
                The node with the given external ID if it exists.
            """
            if external_id is None:
                return None

            nodes: Optional[List[DBNode]] = cls.query.filter_by(external_id=external_id)
            return nodes.first() if len(nodes) == 1 else None

    class DBEdge(declarative_meta):
        """
        Declarative database object model representing an edge.
        """

        # Metaclass definition
        # ------------------------------------------------------------

        # __bind_key__ = bind_key  # Variable name must not be changed.
        __tablename__ = "edges"  # Variable name must not be changed.

        _creation_date = db.Column(db.Date,
                                   nullable=False,
                                   default=datetime.date.today)

        source_name = db.Column(db.String,
                                db.ForeignKey("nodes.name"),
                                db.CheckConstraint("source_name < target_name"),
                                primary_key=True)
        target_name = db.Column(db.String,
                                db.ForeignKey("nodes.name"),
                                db.CheckConstraint("source_name < target_name"),
                                primary_key=True)
        weight = db.Column(db.Float,
                           db.CheckConstraint("weight > 0"),
                           default=1)

        # Initialization
        # ------------------------------------------------------------

        def __init__(self, source_name: str, target_name: str, weight: float = 1):
            """
            Initialization.

            Arguments:
                source_name (str): The name of the source node of the edge.
                target_name (str): The name of the target node of the edge.
                weight (float): The weight of the edge.
            """
            if source_name is None or target_name is None or source_name == target_name:
                raise ValueError("Invalid source and target name pair: {} - {}".format(
                    source_name, target_name)
                )

            # Make sure the order is right, we don't want the graph to be directed.
            if source_name < target_name:
                self.source_name = source_name
                self.target_name = target_name
            else:
                self.source_name = target_name
                self.target_name = source_name

            self.weight = weight

        # Special methods
        # ------------------------------------------------------------

        def __repr__(self):
            """
            The string representation of the object.
            """
            return "DBEdge({} <> {})".format(self.source_name, self.target_name)

        # Properties
        # ------------------------------------------------------------

        @property
        def creation_date(self) -> datetime.date:
            """
            The date when the edge was created.
            """
            return self._creation_date

        # Class methods
        # ------------------------------------------------------------

        @classmethod
        def find_by_name(cls, source_name: str, target_name: str) -> Optional["DBEdge"]:
            """
            Returns the `DBEdge` connecting the edges with the given names if such an edge
            currently exists in the database.

            Arguments:
                source_name (str): The name of one of the endpoints of the queried edge.
                target_name (str): The name of the other endpoint of the queried edge.

            Returns:
                The edge connecting the given nodes in the database if such an edge exists.
            """
            if source_name < target_name:
                return cls.query.filter_by(source_name=source_name, target_name=target_name).first()
            else:
                return cls.query.filter_by(source_name=target_name, target_name=source_name).first()

    return GraphDatabaseInterface(session, DBNode, DBEdge)
