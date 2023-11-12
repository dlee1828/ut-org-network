import networkx as nx
import itertools
from copy import deepcopy
import numpy as np
import pandas as pd
# TODO: Remove pandas get_dummies and replace with sklearn one-hotters that are saved to disk

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
    G_eng = deepcopy(G)

    _type = np.asarray(list(nx.get_node_attributes(G_eng, 'type').items()))
    is_student = np.asarray(_type[:,1] == 'student', dtype=np.float32)

    majors = nx.get_node_attributes(G_eng, 'major')
    df_majors = pd.get_dummies(pd.Series(majors), prefix='major')
    major_one_hot = df_majors.reindex(G_eng.nodes()).fillna(0).astype(np.float32).values

    years = nx.get_node_attributes(G_eng, 'grade')
    df_years = pd.get_dummies(pd.Series(years), prefix='grade')
    year_one_hot = df_years.reindex(G_eng.nodes()).fillna(0).astype(np.float32).values

    X = np.column_stack((is_student, major_one_hot, year_one_hot))

    nx.set_node_attributes(G_eng, {node: X[i] for i, node in enumerate(G_eng.nodes())}, 'X')
    nx.set_node_attributes(G_eng, dict(zip(_type[:,0], is_student)), 'class')
    G_eng = nx.relabel_nodes(G_eng, {n:i for i, n in enumerate(G.nodes)})
    id_key = {i:n for i, n in enumerate(G.nodes)}

    feature_key = ['is_student'] + df_majors.columns.tolist() + df_years.columns.tolist()

    return G_eng, feature_key, id_key