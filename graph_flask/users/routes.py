from flask import Blueprint, render_template,request, session, jsonify
from graph_flask.microsoft.utils import  require_microsoft_login  , microsoft_graph_api
from graph_flask.models import User, user_project,db
import json
from graph_flask.main.utils import jsonify_api_headers
from flask_cors import cross_origin
users = Blueprint('users', __name__)



@users.route("/api/activeuser", methods=['GET'])
# @require_microsoft_login
@cross_origin(supports_credentials=True)
def activeuser():
    # return {"testing":["testing1", "testing2", "testing3"]}
    # displayname = session.get("user").name
    # active_user = User.query 
    return jsonify_api_headers(session.get("user"))


@users.route("/api/userslist", methods=['GET'])
@cross_origin(supports_credentials=True)
def userslist():
    return jsonify([user.to_json() for user in User.query.all()])

@users.route("/api/adduser", methods=['GET'])
@require_microsoft_login
def adduser():
      microsoft_graph_api().put_manager_incharge('clarence.yeo@smartproperty.sg','desmond.tan@smartproperty.sg')


@users.route("/api/addmanager", methods=['GET'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def addmanager():
      microsoft_graph_api().put_manager_incharge('clarence.yeo@smartproperty.sg','desmond.tan@smartproperty.sg')


@users.route("/api/deleteuser", methods=['DELETE'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def deleteuser():
    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    enquire_user = User.query.filter_by(displayname=request_value['displayname']).first()

    micrsoft_api = microsoft_graph_api()
    for user in enquire_user.get_all_child_users(): micrsoft_api.delete_folder_permission_user(request_data['id'], user.id)
    user_project_entry = user_project.query.filter_by(user_id= enquire_user.employee_id , project_id=request_data['id']).first()
    db.session.delete(user_project_entry)
    db.session.commit()


    return {}