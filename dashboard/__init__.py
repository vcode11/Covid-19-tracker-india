from flask import Flask

app = Flask(__name__)

from dashboard import routes
