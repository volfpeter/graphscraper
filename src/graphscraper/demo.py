"""
Demo script that shows the basic usage of the graphscraper project
through the usage of the `graphscraper.igraph` module.

Requirements:
    The demo requires the `SQLAlchemy` and `igraph` (`python-igraph` on PyPi) libraries.
"""

from igraph import Graph, Vertex

from graphscraper.igraphwrapper import IGraphNode, IGraphWrapper


def create_graph(named: bool = False):
    g: Graph = Graph.Erdos_Renyi(n=50, p=0.2)
    if named:
        for v in g.vs:
            v["name"] = "Node-{}".format(v.index)
            v["external_id"] = "Node-Ext-{}".format(v.index)
    return IGraphWrapper(g)


def test_named_graph():
    graph: IGraphWrapper = create_graph(True)
    test(graph)


def test_unnamed_graph():
    graph: IGraphWrapper = create_graph(False)
    test(graph)


def test_zachary():
    test(IGraphWrapper(Graph.Famous("Zachary")))


def test(graph: IGraphWrapper):
    print("Name of Joe: {}".format(graph.get_authentic_node_name("Joe")))
    print("Name of 1: {}".format(graph.get_authentic_node_name("1")))
    print("Name of Node-22: {}".format(graph.get_authentic_node_name("Node-22")))

    node_name: str = graph.get_authentic_node_name("5")
    print("Node name for 5: {}".format(node_name))

    vertex: Vertex = graph._wrapped_graph.vs[5]
    print("IGraph neighbors:")
    for index, neighbor in enumerate(vertex.neighbors()):
        try:
            print("  - Neighbor {}: {}, {}".format(index, neighbor["name"], neighbor.index))
        except KeyError:
            print("  - Neighbor {}: {}".format(index, neighbor.index))

    node: IGraphNode = graph.nodes.get_node_by_name(node_name, can_validate_and_load=True)
    print("Graph neighbors:")
    for index, neighbor in enumerate(node.neighbors):
        print("  - Neighbor {}: {}, {}, {}".format(index, neighbor.name, neighbor.igraph_index, neighbor.index))


def test_spotify_artist_graph(client_id, client_key, artist_names):
    from graphscraper.spotifyartist import SpotifyArtistGraph
    from graphscraper.spotifyartist import SpotifyArtistNode
    graph: SpotifyArtistGraph = SpotifyArtistGraph(client_id, client_key)
    for artist_name in artist_names:
        print("Querying {}".format(artist_name))
        node: SpotifyArtistNode = graph.nodes.get_node_by_name(artist_name, can_validate_and_load=True)
        if node is not None:
            print("Queried name: {artist_name} | Artist name: {node.name} | Spotify ID: {node.external_id}"
                  "\nNeighbors:".format(artist_name=artist_name, node=node))
            for neighbor in node.neighbors:
                print("  - {node.name}, {node.external_id}".format(node=neighbor))
        else:
            print("Artist not found for queried name: {}".format(artist_name))


def demo():
    test_unnamed_graph()
    test_named_graph()
    test_zachary()
