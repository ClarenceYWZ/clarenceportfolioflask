import os
import uuid
from os import uname_result
import msal
from flask import Blueprint, render_template, redirect,url_for, request, session, jsonify, Request
from graph_flask.zoom.utils import zoom_api
import requests

import graph_flask.config as config
import json
zoom = Blueprint('zoom', __name__)


@zoom.route('/zoomredirect')
def zoomredirect():
    code = request.args.get('code')

    # redirect_full_path= request.base_url

    return redirect(url_for('zoom.zoomapi'))

@zoom.route('/zoomlogin')
def zoomlogin():
    authorize_uri= zoom_api.authorize_uri
    return redirect(authorize_uri)

@zoom.route('/zoomapi')
def zoomapi():

    testing = zoom_api()
    
    return testing.get_all_user()

