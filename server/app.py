from flask import Flask
import numpy as np


app = Flask(__name__)

@app.route('/')
def hello_world():
    s = str(np.array([1, 2, 3]))
    return s
