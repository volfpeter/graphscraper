"""
Graph specialization that uses Spotify's Artist API as the external data source.

The Spotify API client implementation is based on "https://github.com/steinitzu/spotify-api".

Requirements:
    - The `requests` module is required by this graph implementation (`pip install requests`).
    - If the graph needs to create a default database on its own, then `sqlalchemy` is required.
"""

from typing import Dict, List, Optional

import time
from collections import namedtuple

import requests
from requests.auth import HTTPBasicAuth

from graphscraper.db import create_graph_database_interface, GraphDatabaseInterface
from graphscraper.base import Graph, Node, NodeList


class SpotifyArtistGraphError(Exception):
    """
    Specialized error thrown by the Spotify artist graph implementation.
    """
    pass


NameExternalIDPair = namedtuple("NameIDPair", ["name", "external_id"])
"""
Tuple that holds a `name` and an `external_id` property.
"""


class SpotifyArtistGraph(Graph):
    """
    Graph specialization that uses Spotify's Artist API as the external data source.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self,
                 client_id: str,
                 client_key: str,
                 neighbor_count: int = 6,
                 database: Optional[GraphDatabaseInterface] = None):
        """
        Initialization.

        The graph requires a valid Spotify API client ID and key pair to work.

        Arguments:
            client_id (str): The Spotify API client ID to use.
            client_key (str): The Spotify API cliend secret key corresponding to the client ID.
            neighbor_count (int): The number of neighbors to load for any given node.
            database (Optional[GraphDatabaseInterface]): The database interface the graph is using.
        """
        if database is None:
            database = SpotifyArtistGraph.create_default_database()

        super(SpotifyArtistGraph, self).__init__(database)

        self._client: SpotifyClient = SpotifyClient(client_id, client_key)
        """
        The Spotify web API client to use to request data.
        """
        self._neighbor_count: int = neighbor_count
        """
        The number of neighbors to load for any given node.
        """

    # Static methods
    # ------------------------------------------------------------

    @property
    def client(self) -> "SpotifyClient":
        """
        The Spotify web API client to use to request data.
        """
        return self._client

    @property
    def neighbor_count(self) -> int:
        """
        The number of neighbors to load for any given node.
        """
        return self._neighbor_count

    # Static methods
    # ------------------------------------------------------------

    @staticmethod
    def create_default_database(reset: bool = False) -> GraphDatabaseInterface:
        """
        Creates and returns a default SQLAlchemy database interface to use.

        Arguments:
            reset (bool): Whether to reset the database if it happens to exist already.
        """
        import sqlalchemy
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        Base = declarative_base()
        engine = sqlalchemy.create_engine("sqlite:///SpotifyArtistGraph.db", poolclass=StaticPool)
        Session = sessionmaker(bind=engine)

        dbi: GraphDatabaseInterface = create_graph_database_interface(
            sqlalchemy, Session(), Base, sqlalchemy.orm.relationship
        )

        if reset:
            Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        return dbi

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
        items: List[NameExternalIDPair] = self._client.search_artists_by_name(node_name)
        return items[0].name if len(items) > 0 else None

    # Private methods
    # ------------------------------------------------------------

    def _create_node_list(self) -> NodeList:
        """
        Called during the initialization of the graph instance,
        creates and returns the node list of the graph.
        """
        return SpotifyArtistNodeList(self)


class SpotifyArtistNode(Node):
    """
    `Node` extension that loads its neighbors from Spotify using the Artist API.
    """

    _NEIGHBORS_TO_LOAD: int = 6
    """
    The number of neighbors to load from the Spotify web API for a node.
    """

    # Initialization
    # ------------------------------------------------------------

    def __init__(self, graph: SpotifyArtistGraph, index: int, name: str, external_id: Optional[str] = None):
        """
        Initialization.

        Arguments:
             graph (Graph): The graph that owns this node.
             index (int): The unique index of the node in the graph.
             name (str): The name of the node.
             external_id (Optional[str]): The external ID of the node.
        """
        if external_id is None:
            raise SpotifyArtistGraphError(
                "{} must always have an external ID.".format(self.__class__.__name__))

        super(SpotifyArtistNode, self).__init__(graph, index, name, external_id)

    # Private methods
    # ------------------------------------------------------------

    def _load_neighbors_from_external_source(self) -> None:
        """
        Loads the neighbors of the node from the igraph `Graph` instance that is
        wrapped by the graph that has this node.
        """
        graph: SpotifyArtistGraph = self._graph
        items: List[NameExternalIDPair] = graph.client.similar_artists(self.external_id)

        limit: int = graph.neighbor_count if graph.neighbor_count > 0 else self._NEIGHBORS_TO_LOAD
        if len(items) > limit:
            del items[limit:]

        for item in items:
            neighbor: SpotifyArtistNode = graph.nodes.get_node_by_name(item.name,
                                                                       can_validate_and_load=True,
                                                                       external_id=item.external_id)
            graph.add_edge(self, neighbor)


class SpotifyArtistNodeList(NodeList):
    """
    `NodeList` extenstion that creates `SpotifyArtistNode` instances.
    """

    # Private methods
    # ------------------------------------------------------------

    def _create_node(self, index: int, name: str, external_id: Optional[str] = None) -> SpotifyArtistNode:
        """
        Returns a new `SpotifyArtistNode` instance with the given index and name.

        Arguments:
            index (int): The index of the node to create.
            name (str): The name of the node to create.
            external_id (Optional[str]): The external ID of the node.
        """
        if external_id is None:
            graph: SpotifyArtistGraph = self._graph
            items: List[NameExternalIDPair] = graph.client.search_artists_by_name(name)
            for item in items:
                if item.name == name:
                    external_id = item.external_id
                    break

        return SpotifyArtistNode(graph=self._graph, index=index, name=name, external_id=external_id)


class SpotifyClientError(Exception):
    """
    Specialized error that is raised by Spotify client components.
    """
    pass


class SpotifyClientTokenWrapper(object):
    """
    Automatized Spotify web API Client Credentials Flow authentication implementation.
    """

    _GRANT_TYPE: str = "client_credentials"
    """
    The grant type for Client Credentials Flow authentication.
    """

    _REFRESH_THRESHOLD: int = 60
    """
    The minimum number of seconds the authentication token must be valid for.
    If the token is valid for less time than this value, then it will be refreshed automatically.
    """

    _TOKEN_URL: str = "https://accounts.spotify.com/api/token"
    """
    The URL where authentication tokens can be requested from.
    """

    def __init__(self, client_id: str, client_key: str):
        """
        Initialization.

        Arguments:
            client_id (str): The Spotify API client ID to use.
            client_key (str): The Spotify API cliend secret key corresponding to the client ID.
        """
        self._client_id: str = client_id
        """
        The Spotify API client ID to use.
        """
        self._client_key: str = client_key
        """
        The Spotify API cliend secret key corresponding to the client ID.
        """
        self._token: Optional[Dict] = None
        """
        The current authentication token.
        """
        self._token_expires_at: float = 0
        """
        The second when the already existing token expires.
        """

    @property
    def access_token(self) -> str:
        """
        The access token stored within the requested token.
        """
        if self._token_expires_at < time.time() + self._REFRESH_THRESHOLD:
            self.request_token()

        return self._token["access_token"]

    def request_token(self) -> None:
        """
        Requests a new Client Credentials Flow authentication token from the Spotify API
        and stores it in the `token` property of the object.

        Raises:
            requests.HTTPError: If an HTTP error occurred during the request.
        """
        response: requests.Response = requests.post(
            self._TOKEN_URL,
            auth=HTTPBasicAuth(self._client_id, self._client_key),
            data={"grant_type": self._GRANT_TYPE},
            verify=True
        )
        response.raise_for_status()
        self._token = response.json()
        self._token_expires_at = time.time() + self._token["expires_in"]


class SpotifyClient(object):
    """
    Spotify web API client.
    """

    _API_URL_TEMPLATE: str = "https://api.spotify.com/v1/{}"
    """
    URL template to use to access the Spotify web API.
    """

    def __init__(self, client_id: str, client_key: str):
        """
        Initialization.

        Arguments:
            client_id (str): The Spotify API client ID to use.
            client_key (str): The Spotify API cliend secret key corresponding to the client ID.
        """
        self._token: SpotifyClientTokenWrapper = SpotifyClientTokenWrapper(client_id, client_key)
        """
        The client token wrapper to use to access the Spotify web API.
        """

    def search_artists_by_name(self, artist_name: str, limit: int = 5) -> List[NameExternalIDPair]:
        """
        Returns zero or more artist name - external ID pairs that match the specified artist name.

        Arguments:
            artist_name (str): The artist name to search in the Spotify API.
            limit (int): The maximum number of results to return.

        Returns:
            Zero or more artist name - external ID pairs.

        Raises:
            requests.HTTPError: If an HTTP error occurred during the request.
            SpotifyClientError: If an invalid item is found.
        """
        response: requests.Response = requests.get(
            self._API_URL_TEMPLATE.format("search"),
            params={"q": artist_name, "type": "artist", "limit": limit},
            headers={"Authorization": "Bearer {}".format(self._token.access_token)}
        )

        # TODO: handle API rate limiting

        response.raise_for_status()
        if not response.text:
            return []

        result: List[NameExternalIDPair] = []
        data: List[Dict] = response.json()["artists"]["items"]
        for artist in data:
            artist = NameExternalIDPair(artist["name"], artist["id"])
            if artist.name is None or artist.external_id is None:
                raise SpotifyClientError("Name or ID is missing")
            result.append(artist)

        return result

    def similar_artists(self, artist_id: str) -> List[NameExternalIDPair]:
        """
        Returns zero or more similar artists (in the form of artist name - external ID pairs)
        to the one corresponding to the given artist ID.

        Arguments:
            artist_id ([str]): The Spotify ID of the artist for whom similar artists are requested.

        Returns:
            Zero or more artist name - external ID pairs.

        Raises:
            requests.HTTPError: If an HTTP error occurred during the request.
            SpotifyClientError: If an invalid item is found.
        """
        response: requests.Response = requests.get(
            self._API_URL_TEMPLATE.format("artists/{}/related-artists".format(artist_id)),
            headers={"Authorization": "Bearer {}".format(self._token.access_token)}
        )

        # TODO: handle API rate limiting

        response.raise_for_status()
        if not response.text:
            return []

        result: List[NameExternalIDPair] = []
        data: List[Dict] = response.json()["artists"]
        for artist in data:
            artist = NameExternalIDPair(artist["name"], artist["id"])
            if artist.name is None or artist.external_id is None:
                raise SpotifyClientError("Name or ID is missing")
            result.append(artist)

        return result
