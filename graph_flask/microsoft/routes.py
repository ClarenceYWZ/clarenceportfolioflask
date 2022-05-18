import os
import io
from flask import Blueprint, render_template,request, session
from graph_flask.microsoft.utils import  require_microsoft_login, microsoft_graph_api, require_microsoft_graph_login, folder_graph_api
from graph_flask.main.utils import jsonify_api_headers
from graph_flask import mail
import pandas as pd
from datetime import date, timedelta,datetime
import json
from graph_flask.models import User, smart_project_listing,db
from graph_flask.views.subscriptions_view import SubscriptionsAPI
from graph_flask.printing_postage.utils import printing_class
from flask_mail import Message
import requests

import graph_flask.config as config
microsoft = Blueprint('microsoft', __name__)
microsoft.add_url_rule('/graphapi', view_func=SubscriptionsAPI.as_view("subscriptions_view"), methods=['GET'])

@microsoft.route("/graphapi/activeuser", methods=['GET' ,'POST'])
# @require_microsoft_graph_login
def graphactiveuser():
    # return {"testing":["testing1", "testing2", "testing3"]}
    # displayname = session.get("user").name
    # active_user = User.query 
    activeuser =microsoft_graph_api().get_graph_api("https://graph.microsoft.com/v1.0/me")
    return jsonify_api_headers(activeuser)


@microsoft.route("/api/addplanner", methods=['POST'])

def addplanner():
    request_data = json.loads(request.data)
    print (request_data)
    graphdata = microsoft_graph_api().planner_graph_api().post_new_planner_task(plannerName=request_data['plannerName'], bucketName=request_data['bucketname'],
                                                            title= request_data['title'],description= request_data['description'], assignUsers= request_data['assignUsers'],
                                                            checklistitems=request_data['checklistitems'],assignDate=request_data['assignDate'], dueDate=request_data['dueDate'])

    return graphdata


@microsoft.route("/graphapi/testing")
# @require_microsoft_graph_login
def graphapitest():
    # testing = folder_graph_api()
    # file_pd = testing.get_lastest_excel_file_to_pandas(site_id=testing.invoice_site_id, list_id=testing.stationary_list_id, 
    # file_path=r"PHOTOCOPIER FRANKING REPORT\FRANKING\2022\03 - MAR-22", search_file_name=".csv")
    # print(file_pd)
    report_date = datetime(2022,2,28)
    test = printing_class(report_date=report_date)
    # test.import_all_monthly_report()
    
    return ({})


