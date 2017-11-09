"""
Base graph implementation that builds a graph by loading data from some data source, caching the
retrieved data in a database of your choice in the meantime.

The building blocks of the graph implementation are nodes and edges that are stored in node and
edge lists respectively that are bound together by the graph itself.

You can build on this base graph implementation by implementing i) the graph method that turns a
(potentially incorrect) node name into a valid node name and ii) the node method that returns the
neighbors of the given node.
"""

# Imports
# ------------------------------------------------------------

from operator import attrgetter
from typing import Dict, List, Optional, Tuple, Union

from graphscraper.db import DBEdge, DBNode, GraphDatabaseInterface
from graphscraper.eventdispatcher import Event, EventDispatcher

# Module constants
# ------------------------------------------------------------

__author__ = 'Peter Volf'

# Classes
# ------------------------------------------------------------


class Node(EventDispatcher):
    """
    Node implementation that is able to load its neighbors from a data source and
    store the loaded data in a local database.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, graph: "Graph", index: int, name: str, external_id: Optional[str] = None):
        """
        Initialization.

        Arguments:
             graph (Graph): The graph that owns this node.
             index (int): The unique index of the node in the graph.
             name (str): The name of the node.
             external_id (Optional[str]): The external ID of the node.
        """
        EventDispatcher.__init__(self)

        self._are_neighbors_loaded: bool = False
        """Whether the neighbors of the node have been loaded from the local cache."""
        self._graph: "Graph" = graph
        """The graph that owns this node."""
        self._index: int = index
        """The unique index of the node in the graph."""
        self._neighbors: Dict[(int, int), Edge] = {}
        """Dictionary mapping node index tuples to the corresponding edge."""

        self.are_neighbors_cached: bool = False
        """Whether the neighbors of the node have already been added to the local cache."""
        self.name: str = name
        """The name of the node."""
        self.external_id: Optional[str] = external_id.strip() if external_id is not None else None
        """The external ID of the node."""

    # Properties
    # ------------------------------------------------------------

    @property
    def degree(self) -> int:
        """
        The degree of the node.
        """
        self._load_neighbors()
        return len(self._neighbors)

    @property
    def index(self) -> int:
        """
        The unique index of the node in the graph.
        """
        return self._index

    @property
    def neighbors(self) -> List['Node']:
        """
        The list of neighbors of the node.
        """
        self._load_neighbors()
        return [edge.source if edge.source != self else edge.target
                for edge in self._neighbors.values()]

    # Public methods
    # ------------------------------------------------------------

    def add_neighbor(self, edge: "Edge") -> None:
        """
        Adds a new neighbor to the node.

        Arguments:
            edge (Edge): The edge that would connect this node with its neighbor.
        """
        if edge is None or (edge.source != self and edge.target != self):
            return

        if edge.source == self:
            other: Node = edge.target
        elif edge.target == self:
            other: Node = edge.source
        else:
            raise ValueError("Tried to add a neighbor with an invalid edge.")

        edge_key: Tuple(int, int) = edge.key

        # The graph is considered undirected, check neighbor existence accordingly.
        if self._neighbors.get(edge_key) or self._neighbors.get((edge_key[1], edge_key[0])):
            return  # The neighbor is already added.

        self._neighbors[edge_key] = edge
        self.dispatch_event(NeighborAddedEvent(other))

    # Private methods
    # ------------------------------------------------------------

    def _load_neighbors(self) -> None:
        """
        Loads all neighbors of the node from the local database and
        from the external data source if needed.
        """
        if not self.are_neighbors_cached:
            self._load_neighbors_from_external_source()
            db: GraphDatabaseInterface = self._graph.database
            db_node: DBNode = db.Node.find_by_name(self.name)
            db_node.are_neighbors_cached = True
            db.session.commit()
            self.are_neighbors_cached = True
        if not self._are_neighbors_loaded:
            self._load_neighbors_from_database()

    def _load_neighbors_from_database(self) -> None:
        """
        Loads the neighbors of the node from the local database.
        """
        self._are_neighbors_loaded = True

        graph: Graph = self._graph
        neighbors: List[DBNode] = graph.database.Node.find_by_name(self.name).neighbors
        nodes: NodeList = graph.nodes

        for db_node in neighbors:
            graph.add_node(db_node.name, db_node.external_id)
            neighbor: Node = nodes.get_node_by_name(db_node.name)
            graph.add_edge(self, neighbor, 1, False)

    def _load_neighbors_from_external_source(self) -> None:
        """
        Loads the neighbors of the node from the external data source.
        """
        # The default implementation is empty, Node relies on a database filled with data.
        # Override this method in child classes to let the node load its neighbors from
        # an external data source.
        pass


class Edge(object):
    """
    Graph edge.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, source: Node, target: Node, weight: float = 1):
        """
        Initialization.

        Arguments:
            source (Node): The source node of the edge.
            target (Node): The target node of the edge.
            weight (float): The weight of the edge.
        """
        if not isinstance(source, Node):
            raise TypeError("Invalid source node: {}".format(source))
        if not isinstance(target, Node):
            raise TypeError("Invalid target node: {}".format(target))
        if (not isinstance(weight, float) and not isinstance(weight, int)) or weight <= 0:
            raise TypeError("Invalid edge weight: {}".format(weight))
        if source.index == target.index:
            raise ValueError("Creating a loop edge is not allowed.")

        self._source: Node = source
        """The source node of the edge."""
        self._target: Node = target
        """The target node of the edge."""
        self._weight: float = weight
        """The weight of the edge."""

        source.add_neighbor(self)
        target.add_neighbor(self)

    # Properties
    # ------------------------------------------------------------

    @property
    def key(self) -> Tuple[int, int]:
        """
        The unique identifier of the edge consisting of the indexes of its
        source and target nodes.
        """
        return self._source.index, self._target.index

    @property
    def source(self) -> Node:
        """
        The source node of the edge.
        """
        return self._source

    @property
    def target(self) -> Node:
        """
        The target node of the edge.
        """
        return self._target

    @property
    def weight(self) -> float:
        """
        The weight of the edge.
        """
        return self._weight


class NodeList(object):
    """
    Container that stores `Node` instances.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, graph: "Graph"):
        """
        Initialization.

        Arguments:
            graph (Graph): The graph the node list belongs to.
        """
        self._graph: Graph = graph
        """The graph the node list belongs to."""
        self._nodes: Dict[int, Node] = {}
        """Storage for the nodes of node list as a node index to node instance mapping."""
        self._node_name_map: Dict[str, Node] = {}
        """Dictionary that maps node names to node instances."""

    # Special methods
    # ------------------------------------------------------------

    def __len__(self) -> int:
        """
        Returns the number of items in the container.
        """
        return len(self._nodes)

    def __getitem__(self, key: Union[int, str]) -> Node:
        """
        Returns the node corresponding to the given key.

        If the given key is an integer, then the node with the given index will be returned.

        If the given key is a string, then the node with the given name will be returned.

        Arguments:
            key (Union[int, str]): The key that identifies the node to return.

        Raises:
            IndexError: If the index is invalid or out of range.
        """
        node: Node = None
        if isinstance(key, int):
            node = self._nodes.get(key)
        if isinstance(key, str):
            node = self._node_name_map.get(key)

        if node is None:
            raise IndexError("Invalid key.")

        return node

    # Public methods
    # ------------------------------------------------------------

    def add_node_by_name(self, node_name: str, external_id: Optional[str] = None) -> None:
        """
        Adds a new node to the graph if it doesn't exist.

        Arguments:
            node_name (str): The name of the node to add.
            external_id (Optional[str]): The external ID of the node.
        """
        if node_name is None:
            return

        node_name = node_name.strip()
        if len(node_name) == 0:
            return

        node: Node = self.get_node_by_name(node_name, external_id=external_id)
        if node is None:
            self._internal_add_node(node_name=node_name,
                                    external_id=external_id,
                                    are_neighbors_cached=False,
                                    add_to_cache=True)

    def get_node(self, index: int) -> Optional[Node]:
        """
        Returns the node with the given index if such a node currently exists in the node list.

        Arguments:
            index (int): The index of the queried node.

        Returns:
            The node with the given index if such a node currently exists in the node list,
            `None` otherwise.
        """
        return self._nodes.get(index)

    def get_node_by_name(self, node_name: str,
                         can_validate_and_load: bool = False,
                         external_id: Optional[str] = None) -> Optional[Node]:
        """
        Returns the node with the given name if it exists either in the graph
        or in its database cache or `None` otherwise.

        Arguments:
            node_name (str): The name of the node to return.
            can_validate_and_load (bool): Whether `self._graph.get_authentic_node_name(node_name)`
                                          can be called to validate the node name and add the node
                                          to the graph if the node name is valid.
            external_id (Optional[str]): An optional external ID that is used only if there no node
                                         with the given name in the graph or in the cache and
                                         `can_validate_and_load` is `True`.

        Returns:
            The node with the given name if it exists either in the graph
            or in its database cache, `None` otherwise.
        """
        node: Node = self._node_name_map.get(node_name)
        if node is not None:
            return node

        db_node: DBNode = self._graph.database.Node.find_by_name(node_name)
        if db_node is None:
            if can_validate_and_load:
                node_name = self._graph.get_authentic_node_name(node_name)
                if node_name is not None:
                    db_node = self._graph.database.Node.find_by_name(node_name)
                    if db_node is None:
                        self._internal_add_node(node_name=node_name,
                                                external_id=external_id,
                                                are_neighbors_cached=False,
                                                add_to_cache=True)
                    else:
                        self._internal_add_node(node_name=db_node.name,
                                                external_id=db_node.external_id,
                                                are_neighbors_cached=db_node.are_neighbors_cached,
                                                add_to_cache=False)
            else:
                return None
        else:
            self._internal_add_node(node_name=db_node.name,
                                    external_id=db_node.external_id,
                                    are_neighbors_cached=db_node.are_neighbors_cached,
                                    add_to_cache=False)

        node = self._node_name_map.get(node_name)

        # Trying to load the cached neighbors of the created node from the database could
        # cause a very-very-very deep recursion, so don't even think about doing it here.

        return node

    # Private methods
    # ------------------------------------------------------------

    def _create_node(self, index: int, name: str, external_id: Optional[str] = None) -> Node:
        """
        Returns a new `Node` instance with the given index and name.

        Arguments:
            index (int): The index of the node to create.
            name (str): The name of the node to create.
            external_id (Optional[str]): The external ID of the node.
        """
        return Node(graph=self._graph, index=index, name=name, external_id=external_id)

    def _internal_add_node(self,
                           node_name: str,
                           external_id: Optional[str] = None,
                           are_neighbors_cached: bool = False,
                           add_to_cache: bool = False) -> None:
        """
        Adds a node with the given name to the graph without checking whether it already exists or not.

        Arguments:
            node_name (str): The name of the node to add.
            external_id (Optional[str]): The external ID of the node.
            are_neighbors_cached (bool): Whether the neighbors of the node have already been cached.
            add_to_cache (bool): Whether the node should also be created in the local cache.
        """
        index: int = len(self)
        node: Node = self._create_node(index, node_name, external_id)
        node.are_neighbors_cached = are_neighbors_cached
        self._nodes[index] = node
        self._node_name_map[node_name] = node

        if add_to_cache:
            db: GraphDatabaseInterface = self._graph.database
            db_node: DBNode = db.Node.find_by_name(node.name)
            if db_node is None:
                db_node = db.Node(node.name, node.external_id)
                db_node.are_neighbors_cached = False
                db.session.add(db_node)
                db.session.commit()


class EdgeList(object):
    """
    Container that stores `Edge` instances.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, graph: "Graph"):
        """
        Initialization.

        Arguments:
            graph (Graph): The graph the edge list belongs to.
        """
        self._graph: "Graph" = graph
        """The graph the edge list belongs to."""
        self._edges: Dict[(int, int), Edge] = {}
        """Edge key to edge instance mapping."""

    # Special methods
    # ------------------------------------------------------------

    def __len__(self) -> int:
        """
        Returns the number of edge instances contained by the edge list.
        """
        return len(self._edges)

    def __getitem__(self, key: Union[Tuple[int, int],
                                     Tuple[str, str],
                                     Tuple[Node, Node]]) -> Optional[Edge]:
        """
        Returns the edge corresponding to the given key.

        If the given key is a tuple of nodes or node indexes, then the edge connecting the two
        nodes will be returned if such an edge exists.

        If the given key is a tuple of node names, then the edge connecting the corresponding
        nodes will be returned if such an edge exists.

        Arguments:
            key (Union[Tuple[int, int], Tuple[str, str], Tuple[Node, Node]]): The key identifying the edge to return.
        """
        if isinstance(key[0], Node) and isinstance(key[1], Node):
            return self.get_edge(key[0], key[1])
        elif isinstance(key[0], int) and isinstance(key[1], int):
            return self.get_edge_by_index(key[0], key[1])
        elif isinstance(key[0], str) and isinstance(key[1], str):
            return self.get_edge_by_name(key[0], key[1])
        raise ValueError("Invalid edge key: {}".format(key))

    # Properties
    # ------------------------------------------------------------

    @property
    def edge_list(self) -> List[Edge]:
        """
        The ordered list of edges in the container.
        """
        return [edge for edge in sorted(self._edges.values(), key=attrgetter("key"))]

    # Public properties
    # ------------------------------------------------------------

    def add_edge(self,
                 source: Node,
                 target: Node,
                 weight: float = 1,
                 save_to_cache: bool = True) -> None:
        """
        Adds an edge to the edge list that will connect the specified nodes.

        Arguments:
            source (Node): The source node of the edge.
            target (Node): The target node of the edge.
            weight (float): The weight of the created edge.
            save_to_cache (bool): Whether the edge should be saved to the local database.
        """
        if not isinstance(source, Node):
            raise TypeError("Invalid source: expected Node instance, got {}.".format(source))
        if not isinstance(target, Node):
            raise TypeError("Invalid target: expected Node instance, got {}.".format(target))

        if source.index == target.index or\
           self.get_edge_by_index(source.index, target.index) is not None:
            return

        self._edges[(source.index, target.index)] = Edge(source, target, weight)

        if save_to_cache:
            should_commit: bool = False
            database: GraphDatabaseInterface = self._graph.database
            db_edge: DBEdge = database.Edge.find_by_name(source.name, target.name)
            if db_edge is None:
                database.session.add(database.Edge(source.name, target.name, weight))
                should_commit = True
            elif db_edge.weight != weight:
                db_edge.weight = weight
                should_commit = True

            if should_commit:
                database.session.commit()

    def get_edge(self, source: Node, target: Node) -> Optional[Edge]:
        """
        Returns the edge connection the given nodes if such an edge exists.

        Arguments:
            source (Node): One of the endpoints of the queried edge.
            target (Node): The other endpoint of the queried edge.

        Returns:
            Returns the edge connection the given nodes
            or `None` if no such node exists.
        """
        return self.get_edge_by_index(source.index, target.index)

    def get_edge_by_index(self, source_index: int, target_index: int) -> Optional[Edge]:
        """
        Returns the edge connecting the nodes with the specified indices if such an edge exists.

        Arguments:
            source_index (int): The index of one of the endpoints of queried edge.
            target_index (int): The index of the other endpoint of the queried edge.

        Returns:
            The edge connecting the nodes with the specified indices
            or `None` if no such node exists.
        """
        edge = self._edges.get((source_index, target_index))
        if edge is not None:
            return edge
        return self._edges.get((target_index, source_index))

    def get_edge_by_name(self, source_name: str, target_name: str) -> Optional[Edge]:
        """
        Returns the edge connecting the nodes with the specified names if such an edge exists.

        Arguments:
            source_name (str): The name of one of the endpoints of queried edge.
            target_name (str): The name of the other endpoint of the queried edge.

        Returns:
            The edge connecting the nodes with the specified names
            or `None` if no such node exists.
        """
        nodes: NodeList = self._graph.nodes
        source: Optional[Node] = nodes.get_node_by_name(source_name)
        if source is None:
            return None
        target: Optional[Node] = nodes.get_node_by_name(target_name)
        if target is None:
            return None
        return self.get_edge_by_index(source.index, target.index)


class Graph(object):
    """
    Undirected graph implementation.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, database: GraphDatabaseInterface):
        """
        Initialization.

        Arguments:
            database (GraphDatabaseInterface): The database interface the graph is using.
        """
        self._edges: EdgeList = self._create_edge_ist()
        """The edge list of the graph."""
        self._nodes: NodeList = self._create_node_list()
        """The node list of the graph."""

        self.database: GraphDatabaseInterface = database
        """The database interface the graph is using."""

    # Properties
    # ------------------------------------------------------------

    @property
    def edges(self) -> EdgeList:
        """
        The edge list of the graph.
        """
        return self._edges

    @property
    def nodes(self) -> NodeList:
        """
        The node list of the graph.
        """
        return self._nodes

    # Public methods
    # ------------------------------------------------------------

    def add_edge(self, source: Node,
                 target: Node,
                 weight: float = 1,
                 save_to_cache: bool = True) -> None:
        """
        Adds an edge between the specified nodes of the graph.

        Arguments:
            source (Node): The source node of the edge to add.
            target (Node): The target node of the edge to add.
            weight (float): The weight of the edge.
            save_to_cache (bool): Whether the edge should be saved to the local database. This
                                  argument is necessary (and `False`) when we load edges from
                                  the local cache.
        """
        if self._edges.get_edge(source, target) is not None:
            return

        self._edges.add_edge(
            source=source,
            target=target,
            weight=weight,
            save_to_cache=save_to_cache
        )

    def add_edge_by_index(self, source_index: int, target_index: int,
                          weight: float, save_to_cache: bool = True) -> None:
        """
        Adds an edge between the nodes with the specified indices to the graph.

        Arguments:
            source_index (int): The index of the source node of the edge to add.
            target_index (int): The index of the target node of the edge to add.
            weight (float): The weight of the edge.
            save_to_cache (bool): Whether the edge should be saved to the local database. This
                                  argument is necessary (and `False`) when we load edges from
                                  the local cache.
        """
        source: Node = self._nodes.get_node(source_index)
        target: Node = self._nodes.get_node(target_index)
        if source is None or target is None:
            return

        self.add_edge(
            source=source,
            target=target,
            weight=weight,
            save_to_cache=save_to_cache
        )

    def add_node(self, node_name: str, external_id: Optional[str] = None) -> None:
        """
        Adds the node with the given name to the graph.

        Arguments:
            node_name (str): The name of the node to add to the graph.
            external_id (Optional[str]): The external ID of the node.
        """
        self._nodes.add_node_by_name(node_name, external_id)

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
        node: Node = self._nodes.get_node_by_name(node_name)
        return node.name if node is not None else None

    def node_exists(self, node_name: str) -> bool:
        """
        Returns whether a node with the given name exists in the graph.

        This method relies on the value returned by `get_authentic_node_name()` to decide whether
        a node with a certain name exists or not.

        Arguments:
            node_name (str): The name of the node to check.

        Returns:
            `True` if there is a node with the specified name in the graph, `False` otherwise.
        """
        return self.get_authentic_node_name(node_name) is not None

    # Private methods
    # ------------------------------------------------------------

    def _create_edge_ist(self) -> EdgeList:
        """
        Called during the initialization of the graph instance,
        creates and returns the edge list of the graph.
        """
        return EdgeList(self)

    def _create_node_list(self) -> NodeList:
        """
        Called during the initialization of the graph instance,
        creates and returns the node list of the graph.
        """
        return NodeList(self)


class NeighborAddedEvent(Event):
    """
    The event `Node` instances use to let others know that they have received a new neighbor.
    """

    # Class constants
    # ------------------------------------------------------------

    NEIGHBOR_ADDED = "neighborAdded"
    """Dispatched when a neighbor is added to a node through its `add_neighbor()` method."""

    # Initializations
    # ------------------------------------------------------------

    def __init__(self, neighbor: Node):
        """
        Initializations.

        Arguments:
            neighbor (Node): The neighbor that was added to the node.
        """
        super(NeighborAddedEvent, self).__init__(NeighborAddedEvent.NEIGHBOR_ADDED)
        self._neighbor: Node = neighbor
        """The neighbor that was added to the node."""

    # Properties
    # ------------------------------------------------------------

    @property
    def neighbor(self) -> Node:
        """
        The neighbor that was added to the node that dispatched this event.
        """
        return self._neighbor
