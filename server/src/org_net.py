
import numpy as np
from copy import deepcopy
from scipy.sparse import coo_matrix
import dgl.function as fn
import utils
import models
import transform
import itertools
import dgl
import torch
import json
import networkx as nx
from joblib import dump, load

def invert_graph(g, copy_data=True, separate_classes=True, save=False):
    
    # Create negative adj mtx
    u, v = g.edges()
    u, v = u.numpy(), v.numpy()
    edge_index = np.array((u, v))
    adj = coo_matrix((np.ones(g.num_edges()), edge_index))
    adj_neg = 1 - adj.todense() - np.eye(g.num_nodes())
    neg_u, neg_v = np.where(adj_neg != 0)

    # Invert the graph

    inv_g = dgl.graph((neg_u, neg_v), num_nodes=g.num_nodes())
    if copy_data:
        for k in g.ndata:
            inv_g.ndata[k] = g.ndata[k]

    # Find and remove all edges between the same class
    if separate_classes:
        with inv_g.local_scope():
            inv_g.apply_edges(lambda edges: {'diff_class' : edges.src['class'] != edges.dst['class']})
            sep = inv_g.edata['diff_class'].numpy()
        inv_g = dgl.remove_edges(inv_g, np.where(~sep)[0])

    if save:
        dump(inv_g, '../data/G_inv.joblib')
    return inv_g

def create_train_test_split_edge(data):
    # Create a list of positive and negative edges
    u, v = data.edges()
    u, v = u.numpy(), v.numpy()
    edge_index = np.array((u, v))

    neg_data = invert_graph(data)
    neg_u, neg_v = neg_data.edges()
    neg_u, neg_v = neg_u.numpy(), neg_v.numpy()

    # adj = coo_matrix((np.ones(data.num_edges()), edge_index))
    # adj_neg = 1 - adj.todense() - np.eye(data.num_nodes())
    # neg_u, neg_v = np.where(adj_neg != 0)

    # Create train/test edge split
    test_size = int(np.floor(data.num_edges() * 0.1))
    eids = np.random.permutation(np.arange(data.num_edges())) # Create an array of 'edge IDs'

    train_pos_u, train_pos_v = edge_index[:, eids[test_size:]]
    test_pos_u, test_pos_v   = edge_index[:, eids[:test_size]]

    # Sample an equal amount of negative edges from  the graph, split into train/test
    neg_eids = np.random.choice(len(neg_u), data.num_edges())
    test_neg_u, test_neg_v = (
        neg_u[neg_eids[:test_size]],
        neg_v[neg_eids[:test_size]],
    )
    train_neg_u, train_neg_v = (
        neg_u[neg_eids[test_size:]],
        neg_v[neg_eids[test_size:]],
    )

    # Remove test edges from original graph
    train_g = deepcopy(data)
    train_g.remove_edges(eids[:test_size]) # Remove positive edges from the testing set from the network

    train_pos_g = dgl.graph((train_pos_u, train_pos_v), num_nodes=data.num_nodes())
    train_neg_g = dgl.graph((train_neg_u, train_neg_v), num_nodes=data.num_nodes())

    test_pos_g = dgl.graph((test_pos_u, test_pos_v), num_nodes=data.num_nodes())
    test_neg_g = dgl.graph((test_neg_u, test_neg_v), num_nodes=data.num_nodes())

    return train_g, train_pos_g, train_neg_g, test_pos_g, test_neg_g

def clean_graph_pipeline(G, save=True):
    G_eng, feature_dict, id_key = transform.engineer_features(G)
    G = dgl.from_networkx(G_eng, node_attrs=['X', 'class'])
    if save:
        dump(G, '../data/G_clean.joblib')
        dump(id_key, '../data/id_key.joblib')
    return G, id_key

def train_pipeline(G, epochs=1000, save=True):
    train_g, train_pos_g, train_neg_g, test_pos_g, test_neg_g = create_train_test_split_edge(G)
    model = models.GraphSAGE(train_g.ndata["X"].shape[1], 32)
    pred = models.DotPredictor()
    optimizer = torch.optim.Adam(
        itertools.chain(model.parameters(), pred.parameters()), lr=0.01
    )

    # ----------- 4. training -------------------------------- #
    for e in range(epochs + 1):
        # forward
        h = model(train_g, train_g.ndata["X"])
        pos_score = pred(train_pos_g, h)
        neg_score = pred(train_neg_g, h)
        loss = utils.compute_loss(pos_score, neg_score)

        # backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if e % 5 == 0:
            print("In epoch {}, loss: {}".format(e, loss))

        # ----------- 5. check results ------------------------ #
        if e % 100 == 0:
            with torch.no_grad():
                pos_score = pred(test_pos_g, h)
                neg_score = pred(test_neg_g, h)
                print("AUC", utils.compute_auc(pos_score, neg_score))

    if save:
        dump(model, '../data/model.joblib')
    return model

def calc_scores(g, model):
    
    with g.local_scope():
        g.ndata["h"] = model(g, g.ndata['X'])
        # TODO replace this with cosine sim
        g.apply_edges(fn.u_dot_v("h", "h", "score"))
        g.apply_edges(lambda edges: {'diff_class' : edges.src['class'] != edges.dst['class']})
        scores = g.edata["score"][:, 0].detach().numpy()
        class_mask = g.edata['diff_class'].numpy()

        return np.column_stack((scores, class_mask))

def output_pipeline(graph: dgl.DGLGraph, 
                    model, 
                    k: int=5, 
                    threshold: float=0.5,  
                    mode: str='topK',
                    invert=True):
    if mode.lower() not in ['topk', 'threshold', 'all']:
        raise ValueError('Mode must be either \'topK\' or \'threshold\' or \'all\'')


    # Create an inverse of the current graph
    # This way we only generate prediction scores for nodes which aren't connected yet
    if invert:
        graph = invert_graph(graph)

    u, v = graph.edges()
    u, v = u.numpy(), v.numpy()
    # eids = np.arange(g.num_edges())
    edges = np.column_stack((u, v))

    scores = calc_scores(graph, model)

    # Select only the edges which the class of nodes are different
    mask = np.where(scores[:,1])
    scores = scores[mask][:,0]
    edges = edges[mask]

    order = scores.argsort()[::-1] # Sort descending by score

    scores = scores[order]
    edges = edges[order]

    # if mode is top k, take top k scores
    ret = np.column_stack((edges, scores))
    if mode.lower() == 'topk':
        ret = ret[:k]
        return ret
    if mode.lower() == 'threshold':
        thresh = np.where(ret[:,2] > threshold)
        ret = ret[thresh]
        return ret
    
    # Must be all
    return ret  

def node_output_pipelne(graph, node_id, model, k=5, threshold=0.5, mode='topK', inv_precomputed=False):
    # Take the subgraph os stuff only consider node 'node_name'ArithmeticError
    # Pass through output_pipeline
    if mode.lower() not in ['topk', 'threshold', 'all']:
        raise ValueError('Mode must be either \'topK\' or \'threshold\' or \'all\'')


    if not inv_precomputed:
        graph = invert_graph(graph)

    neighborhood = np.concatenate((graph.in_edges(node_id)[0].numpy(), [node_id]))
    sg = graph.subgraph(neighborhood)

    ret = output_pipeline(sg, model, mode='all', invert=False)

    # Map old node_id to sg node_id
    nids = sg.ndata[dgl.NID].numpy()
    ret[:,0:2] = nids[ret[:,0:2].astype('int')]

    ret = ret[np.where(ret[:,0] == node_id)] # Do I need this? Maybe

    if mode.lower() == 'topk':
        ret = ret[:k]
        return ret
    if mode.lower() == 'threshold':
        thresh = np.where(ret[:,2] > threshold)
        ret = ret[thresh]
        return ret
    
    # Must be all, return everything
    return ret
    
def get_reccomendations_for_new_student(name, 
                                        year, 
                                        major, 
                                        list_of_orgs, 
                                        G=None,
                                        model=None, 
                                        id_key=None, 
                                        k=5, 
                                        G_is_inverted=True, 
                                        load_backend=True):
    # Load backend stuff from disk
    if load_backend:
        if G_is_inverted:
            G = load('../data/G_inv.joblib')
        else:
            G = load('../data/G_clean.joblib')
        model = load('../data/model.joblib')
        id_key = load('../data/id_key.joblib')
    elif None in [G, model, id_key]:
        raise ValueError('Backend not loaded from disk, but not properly supplied')
        
    G, id_key, node_id = add_student_to_graph(G, name, year, major, list_of_orgs, id_key, G_is_inverted)
    recs = node_output_pipelne(G, node_id, model, inv_precomputed=G_is_inverted, k=k)

    # Save everything back to disk
    if load_backend:
        if G_is_inverted:
            dump(G, '../data/G_inv.joblib')
        else:
            dump(G, '../data/G_clean.joblib')
        dump(id_key, '../data/id_key.joblib')

    return format_output(recs, id_key)


def add_student_to_graph(G, student_name, year, major, list_of_orgs, id_key, G_is_inverted=False):
    # Clean node
    G_student = nx.Graph()
    G_student.add_node(student_name, grade=year, major=major, type='student')
    G_student_eng, _, __ = transform.engineer_features(G_student, create_new=False)
    G_student_eng = nx.relabel_nodes(G_student_eng, {n:G.number_of_nodes() for n in G_student_eng.nodes})
    node_id = G.number_of_nodes()
    id_key[node_id] = student_name

    # Add node
    X = G.ndata.pop('X')
    cls = G.ndata.pop('class')
    G.add_nodes(1)
    X = torch.cat([X, torch.Tensor(G_student_eng.nodes[node_id]['X']).reshape(1, -1)], dim=0)
    G.ndata['X'] = X
    cls = torch.cat([cls, torch.tensor([G_student_eng.nodes[node_id]['class']])], dim=0)
    G.ndata['class'] = cls

    # Add edges
    u, v = [], []
    for i in np.where(G.ndata['class'].numpy() == 0)[0]:
        if G_is_inverted and (id_key[i] not in list_of_orgs):
            u.append(node_id)
            v.append(i)
        elif (not G_is_inverted) and (id_key[i] in list_of_orgs):
            u.append(node_id)
            v.append(i)
    G.add_edges(u, v)
    G.add_edges(v, u)

    return G, id_key, node_id

def format_output(output, id_key=None, return_ids=False):
    if not return_ids and id_key is None:
        raise ValueError('return_ids is false but id_key is none. Provide a dict from id to name to return names instead of ids')

    formatted = {}

    for n in output[:,0]:
        idx = int(n) if return_ids else id_key[int(n)]

        if n not in formatted.keys():
            formatted[idx] = {}


    for s in output:
        if return_ids:
            formatted[int(s[0])][int(s[1])] = s[2]
        else:
            formatted[id_key[int(s[0])]][id_key[int(s[1])]] = s[2]
       

    return json.dumps(formatted)


        