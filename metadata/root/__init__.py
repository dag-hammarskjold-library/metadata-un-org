from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from metadata import app
from metadata.config import Config
#import importlib

@app.route('/')
def index():
    blueprints = {}

    return render_template('index.html', blueprints=app.blueprints, launched=app.launched, **Config.global_kwargs)