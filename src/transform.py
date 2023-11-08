import networkx as nx
import itertools
from copy import deepcopy
import numpy as np

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


def engineer_features(G):
    # TODO Work on getting this to be more feature agnostic - i.e. take the join of all this stuff and null if not present
    # Also need a stored one-hot 

    # Change type to two features, is_student, and is_org
    G_eng = deepcopy(G)
    _type = np.asarray(list(nx.get_node_attributes(G_eng, 'type').items()))
    is_student = np.asarray(_type[:,1] == 'student', dtype='float32')
    # commitment_limit = list(nx.get_node_attributes(G, 'commitment_limit').values())

    X = np.column_stack([is_student, 1-is_student])
    nx.set_node_attributes(G_eng, dict(zip(_type[:,0], X)), 'X')
    nx.set_node_attributes(G_eng, dict(zip(_type[:,0], is_student)), 'class')

    # TODO Add major in as one-hot

    # TODO Add Year in as one-hot


    return G_eng