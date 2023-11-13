from flask import Flask
import sys
sys.path.append('../src')
sys.path.append('..')

import src.org_net as org_net
import networkx as nx

app = Flask(__name__)

@app.route('/')
def hello_world():
    return "tried adding a few imports"
