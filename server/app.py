from flask import Flask
import sys
sys.path.append('../src')
sys.path.append('..')

import org_net 

app = Flask(__name__)

@app.route('/')
def hello_world():
    return "tried adding a few imports"
