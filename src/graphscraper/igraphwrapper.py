"""
Graph specialization that wraps an igraph `Graph` object.

This graph implementation supports only in-memory SQLite databases.

The wrapped igraph graph must be static once an `IGraphWrapper` starts using it.
(In general it's not a good idea to mutate an igraph `Graph` instance because of
the way igraph stores a graph and indexes its components.)

Requirements:
    - This module requires the `SQLAlchemy` and `igraph` (`python-igraph` on PyPi) libraries.
"""

from typing import List, Optional

from igraph import Graph as IGraph
from igraph import Vertex as IGraphVertex

import sqlalchemy

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from graphscraper.db import create_graph_database_interface, GraphDatabaseInterface
from graphscraper.base import Graph, Node, NodeList


class IGraphWrapper(Graph):
    """
    Graph implementation that takes data from an igraph `Graph` object.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, graph: IGraph):
        """
        Initialization.

        Arguments:
            graph (IGraph): The igraph `Graph` object to wrap.
        """
        super(IGraphWrapper, self).__init__(self._create_memory_database_interface())

        if not isinstance(graph, IGraph):
            raise ValueError("Invalid graph instance provided to IGraphWrapper")

        self._wrapped_graph: IGraph = graph
        """The wrapped igraph `Graph` object."""

    # Properties
    # ------------------------------------------------------------

    @property
    def wrapped_graph(self) -> IGraph:
        """
        The wrapped igraph `Graph` object.
        """
        return self._wrapped_graph

    # Public methods
    # ------------------------------------------------------------

    def get_authentic_node_name(self, node_name: str) -> Optional[str]:
        """
        Returns the exact, authentic node name for the given node name if a node corresponding to
        the given name exists in the graph (maybe not locally yet) or `None` otherwise.

        By default, this method checks whether a node with the given name exists locally in the
        graph and return `node_name` if it does or `None` otherwise.

        In `Graph` extensions that are used by applications where the user can enter potentially
        incorrect node names, this method should be overridden to improve usability.

        Arguments:
            node_name (str): The node name to return the authentic node name for.

        Returns:
            The authentic name of the node corresponding to the given node name or
            `None` if no such node exists.
        """
        # Is there a node with the given name?
        vertex: IGraphVertex = None
        try:
            vertex: IGraphVertex = self._wrapped_graph.vs.find(node_name)
        except ValueError:
            pass

        # Is node_name a node index?
        if vertex is None:
            try:
                vertex: IGraphVertex = self._wrapped_graph.vs[int(node_name)]
            except ValueError:
                return None
            except IndexError:
                return None

        try:
            return vertex["name"]
        except KeyError:
            return str(vertex.index)

    # Private methods
    # ------------------------------------------------------------

    def _create_memory_database_interface(self) -> GraphDatabaseInterface:
        """
        Creates and returns the in-memory database interface the graph will use.
        """
        Base = declarative_base()
        engine = sqlalchemy.create_engine("sqlite://", poolclass=StaticPool)
        Session = sessionmaker(bind=engine)

        dbi: GraphDatabaseInterface = create_graph_database_interface(
            sqlalchemy, Session(), Base, sqlalchemy.orm.relationship
        )

        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        return dbi

    def _create_node_list(self) -> NodeList:
        """
        Called during the initialization of the graph instance,
        creates and returns the node list of the graph.
        """
        return IGraphNodeList(self)


class IGraphNode(Node):
    """
    `Node` extension that takes its neighbors from the corresponding `IGraphWrapper`'s
    wrapped igraph `Graph`.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, graph: IGraphWrapper, index: int, name: str, external_id: Optional[str] = None):
        """
        Initialization.

        Arguments:
             graph (IGraphWrapper): The graph that owns this node.
             index (int): The unique index of the node in the graph.
             name (str): The name of the node.
             external_id (Optional[str]): The external ID of the node.
        """
        super(IGraphNode, self).__init__(graph, index, name, external_id)

        vertex: IGraphVertex = None
        try:
            vertex = graph.wrapped_graph.vs.find(name)
        except ValueError:
            vertex = graph.wrapped_graph.vs[int(name)]

        if vertex is None:
            raise ValueError("The wrapped igraph graph doesn't have a vertex with the given name.")

        self._igraph_index: int = vertex.index
        """The index of the corresponding node in the igraph `Graph` instance."""

    # Properties
    # ------------------------------------------------------------

    @property
    def igraph_index(self) -> int:
        """
        The index of the corresponding node in the igraph `Graph` instance.
        """
        return self._igraph_index

    @property
    def igraph_vertex(self) -> IGraphVertex:
        """
        The vertex in the igraph `Graph` this node represents.
        """
        return self._graph.wrapped_graph.vs[self._igraph_index]

    # Private methods
    # ------------------------------------------------------------

    def _load_neighbors_from_external_source(self) -> None:
        """
        Loads the neighbors of the node from the igraph `Graph` instance that is
        wrapped by the graph that has this node.
        """
        graph: IGraphWrapper = self._graph
        ig_vertex: IGraphVertex = graph.wrapped_graph.vs[self._igraph_index]
        ig_neighbors: List[IGraphVertex] = ig_vertex.neighbors()
        for ig_neighbor in ig_neighbors:
            try:
                name: str = ig_neighbor["name"]
            except KeyError:
                name: str = str(ig_neighbor.index)

            try:
                external_id: Optional[str] = ig_neighbor["external_id"]
            except KeyError:
                external_id: Optional[str] = None

            neighbor: IGraphNode = graph.nodes.get_node_by_name(name,
                                                                can_validate_and_load=True,
                                                                external_id=external_id)
            graph.add_edge(self, neighbor)


class IGraphNodeList(NodeList):
    """
    `NodeList` extension that creates `IGraphNode` instances.
    """

    # Private methods
    # ------------------------------------------------------------

    def _create_node(self, index: int, name: str, external_id: Optional[str] = None) -> IGraphNode:
        """
        Returns a new `IGraphNode` instance with the given index and name.

        Arguments:
            index (int): The index of the node to create.
            name (str): The name of the node to create.
            external_id (Optional[str]): The external ID of the node.
        """
        return IGraphNode(graph=self._graph, index=index, name=name, external_id=external_id)
