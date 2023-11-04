

import networkx as nx
import itertools

def intersect(a1, a2):
    return [n for n in a1 if n in a2]

def create_shared_subgraph(G, type='org'):
    # Create a graph with connections between orgs
    SG = nx.Graph()
    nodes = [n for n in G.nodes if G.nodes[n]['type'] == type]
    SG.add_nodes_from(nodes)
    for n1, n2 in itertools.combinations(nodes, 2):
        # add shared students to an edge
        n1_neighbors = G[n1]
        n2_neighbors = G[n2]

        both_neighbors = intersect(n1_neighbors, n2_neighbors)
        if len(both_neighbors) > 0:
            SG.add_edge(n1, n2, shared_neighbors = both_neighbors)

    return SG