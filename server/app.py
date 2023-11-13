from flask import Flask
import sys
# sys.path.append('../src')
# sys.path.append('..')

import org_net 
import networkx as nx

G = nx.read_graphml('./data/orgnetwork.graphml')

app = Flask(__name__)

@app.route('/')
def hello_world():
    return "tried read_graphml"
