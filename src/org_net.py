
import numpy as np
from copy import deepcopy
from scipy.sparse import coo_matrix
import dgl.function as fn
import utils
import models
import synthetic
import transform
import itertools
import dgl
import torch
import json

def invert_graph(g, copy_data=True, separate_classes=True):
    
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

def clean_graph_pipeline(G):
    G_eng, feature_dict, id_key = transform.engineer_features(G)
    G = dgl.from_networkx(G_eng, node_attrs=['X', 'class'])
    return G, id_key

def train_pipeline(G, epochs=1000):
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
        g = invert_graph(graph)
    else:
        g = deepcopy(graph)

    u, v = g.edges()
    u, v = u.numpy(), v.numpy()
    # eids = np.arange(g.num_edges())
    edges = np.column_stack((u, v))

    scores = calc_scores(g, model)

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

def node_output_pipelne(graph, node_id, model, k=5, threshold=0.5, mode='topK'):
    # Take the subgraph os stuff only consider node 'node_name'ArithmeticError
    # Pass through output_pipeline
    if mode.lower() not in ['topk', 'threshold', 'all']:
        raise ValueError('Mode must be either \'topK\' or \'threshold\' or \'all\'')

    # TODO This needs debugging - create a subgraph with node 'node_id' and all nodes of different class its not connected to already
    g = invert_graph(graph)
    neighborhood = np.concatenate((g.in_edges(node_id)[0].numpy(), [node_id]))
    sg = g.subgraph(neighborhood)
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


        