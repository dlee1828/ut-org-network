from flask import Flask
import sys
# sys.path.append('../src')
# sys.path.append('..')

import org_net 
import networkx as nx

G = nx.read_graphml('./data/orgnetwork.graphml')

G_dgl, id_key = org_net.clean_graph_pipeline(G) # Create synthetic graph and pass to the clean pipeline
inv_graph = org_net.invert_graph(G_dgl, save=True)

model = org_net.train_pipeline(G_dgl, epochs=300)

app = Flask(__name__)

@app.route('/')
def hello_world():
    return "added the other stuff"
