import networkx as nx
import itertools
from copy import deepcopy
import numpy as np
from sklearn.preprocessing import OneHotEncoder as OHE
from joblib import load, dump
#import pandas as pd

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

def engineer_features(G, create_new=True, inplace=True):
    if not inplace:
        G = deepcopy(G)

    feature_key = ['is_student']

    _type = np.asarray(list(nx.get_node_attributes(G, 'type').items()))
    is_student = np.asarray(_type[:,1] == 'student', dtype=np.float32)

    feats = [is_student]
    for feat in ['major', 'grade']:
        feat_data = np.array(list(nx.get_node_attributes(G, feat, default=f'{feat}_NA').values())).reshape(-1, 1)
        if create_new:
            ohe = OHE(handle_unknown='ignore', dtype=np.float32)
            one_hot = ohe.fit_transform(feat_data)
            dump(ohe, f'./data/OHE/{feat}_OHE.joblib')
        else:
            ohe = load(f'./data/OHE/{feat}_OHE.joblib')
            one_hot = ohe.transform(feat_data)
        one_hot = np.array(one_hot.todense())
        feats.append(one_hot)
        feature_key.extend(list(ohe.categories_[0]))

    X = np.column_stack(feats)

    nx.set_node_attributes(G, {node: X[i] for i, node in enumerate(G.nodes())}, 'X')
    nx.set_node_attributes(G, dict(zip(_type[:,0], is_student)), 'class')

    # Relabel (for dgl)
    id_key = {i:n for i, n in enumerate(G.nodes)}
    G = nx.relabel_nodes(G, {n:i for i, n in enumerate(G.nodes)})

    return G, feature_key, id_key