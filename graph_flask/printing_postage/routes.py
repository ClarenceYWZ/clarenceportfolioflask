import os
import uuid
from os import uname_result
import msal
from flask import Blueprint, render_template, redirect,url_for, request, session, jsonify, Request
from graph_flask.main.utils import jsonify_api_headers
from graph_flask.zoom.utils import zoom_api
import requests
from graph_flask.printing_postage.utils import printing_class
import graph_flask.config as config
import json
from datetime import datetime
printing_postage = Blueprint('printing_postage', __name__)


@printing_postage.route('/printing_postage_report')
def printing_postage_report():
    
    report_date = datetime(2022,1,31)
    test = printing_class(report_date=report_date)
    # test.export_to_excel_report()
    test.generate_pdf_breakdown()


    return jsonify_api_headers({'result': 'good'})

