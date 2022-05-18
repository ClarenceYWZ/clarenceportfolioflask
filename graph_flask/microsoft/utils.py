import re, json
import io
import uuid
from importlib_metadata import sys
import msal
import os
from flask import url_for,session,request,redirect
from sqlalchemy import null, true
from graph_flask.main.utils import jsonify_api_headers
from graph_flask.models import User
from functools import wraps
import random
import graph_flask.config as config
import requests
from datetime import datetime
import pandas as pd
from graph_flask.models import User, smart_project_listing, site_staff
from graph_flask import db

def _load_cache():
    cache = msal.SerializableTokenCache()
    
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    

    return cache




def _get_token_on_behalf(request_data):
    # cache = _load_cache() 
    
    tokenEndpoint = f'https://{config.AUTHORITY}/{config.CLIENT_ID}/oauth2/v2.0/token';
  
    result =  msal.ConfidentialClientApplication(config.CLIENT_ID, 
    authority=config.AUTHORITY,
    client_credential=config.CLIENT_SECRET
    ).acquire_token_on_behalf_of(
        user_assertion=request_data['Authorization'].split(' ')[1], scopes= config.SCOPE)
    return result

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    
    return msal.ConfidentialClientApplication(
        config.CLIENT_ID, authority=authority or config.AUTHORITY,
        client_credential=config.CLIENT_SECRET, token_cache=cache)

def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for("main.authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result
    

class microsoft_user :

    def __init__(self):
        self.name = None
        self.role = None
        self.email = None

    def load_user(self):
        """Confirm main authentication by calling Graph and displaying some data."""

        # endpoint = config.RESOURCE + config.API_VERSION + '/me'
        # http_headers = {'client-request-id': str(uuid.uuid4())}
        graphdata = self.session.get("user")
        try:

            self.name = graphdata['name']
            # self.role = graphdata['jobTitle']
            self.email= graphdata['preferred_username']

        except:

            self.name = None
    def __repr__(self):
        return f'Microsoft user ({self.name},{self.email})'

def require_microsoft_login(orig_func):

    @wraps(orig_func)
    def wrapper(*args, **kwargs):

        # from flask import redirect, url_for
        # active_user = microsoft_user()
        # active_user.load_user()
        redirect_url = request.headers.get("Referer") 
        
        if not redirect_url in config.ALLOW_REDIRECT_PATH:
            return jsonify_api_headers({"response" : "unauthorized access"})
        # if not 'user' in session: 
        #     return redirect(url_for('main.login'))

        return orig_func(*args, **kwargs)

    return wrapper

def require_microsoft_graph_login(orig_func):

    @wraps(orig_func)
    def wrapper(*args, **kwargs):

        # from flask import redirect, url_for
        # active_user = microsoft_user()
        # active_user.load_user()
        # redirect_url = request.headers.get("Referer") 
        
        # if not redirect_url in config.ALLOW_REDIRECT_PATH:
        #     return jsonify_api_headers({"response" : "unauthorized access"})
        if not 'user' in session: 
            return redirect(url_for('main.login'))

        return orig_func(*args, **kwargs)

    return wrapper

class microsoft_graph_api:

    def __init__(self):
        request_data = request.headers       
        
        if 'Authorization' in request_data:
            self.token= _get_token_on_behalf(request_data)
        else:
            # self.token =None
            self.token = _get_token_from_cache(config.SCOPE)
        self.site_id = '16dd2991-e08d-41d4-9161-455eff4d1e4e,e0d78cfb-1fcd-4e43-83ec-e48b07d4e867'
        self.list_id = 'fae9f2e4-ee1a-4df7-8310-2bd274d89adc'
        self.smart_hq_site_id = '0aa200a9-86fe-4729-a343-98f4d017d54d'
        self.checklist_list_id = '8c6c2970-297f-4fec-b203-bb9ca8b5732d'
        self.smart_property_list_id = '369e9d3a-3572-428e-a648-7685aef6d33f'
        self.site_staff_group_id ='1aaacaf6-aa6c-42b5-8e94-10e14e8aa31b'
        self.invoice_site_id ='e26b1490-1a53-4fac-b24f-fb68117e8111'
        self.stationary_list_id = '0ab81881-6ed5-45d5-b34c-743f44f144d2'
        if self.token :
            self.active_user = self.token['id_token_claims']['preferred_username']
            self.headers= {'Authorization': 'Bearer ' + self.token['access_token']}
        
    def get_graph_api(self, graph_path, jsonify_bool = True):
        
        graph_data = requests.get(  # Use token to call downstream service
            graph_path,
            headers=self.headers,
        )
        return graph_data.json() if jsonify_bool else graph_data

    def post_graph_api(self, graph_path, json_required):

        # json_required['Authorization']= 'Bearer ' + self.token['access_token']
        
        self.headers['Content-type'] = 'application/json'
        graph_data = requests.post(  # Use token to call downstream service
            graph_path,
            headers= self.headers,
            data = json.dumps(json_required)
        )
        return graph_data.json() if graph_data.text else null

    def patch_graph_api(self, graph_path, json_required={}):

        # json_required['Authorization']= 'Bearer ' + self.token['access_token']
        data = json.dumps(json_required)
        self.headers['Content-type'] = 'application/json'
        
        requests.patch( # Use token to call downstream service
            graph_path,
            headers=self.headers,
            data= data
        )

    def put_graph_api(self, graph_path, content_type=None, json_required={}):

        # json_required['Authorization']= 'Bearer ' + self.token['access_token']
        
        if not content_type :
            self.headers['Content-type'] = 'application/json'
            data = json.dumps(json_required)
        else:
            self.headers['Content-type'] = content_type
            data = json_required
        
        result = requests.put(  # Use token to call downstream service
            graph_path,
            headers=self.headers,
            data=data
        )

        return result
   
    def delete_graph_api(self, graph_path):

        graph_data = requests.delete(  # Use token to call downstream service
            graph_path,
            headers=self.headers
        )

        return graph_data

    def get_group_id(self, groupName):

        graph_path = f'https://graph.microsoft.com/v1.0/groups'
        groupItems = self.get_graph_api(graph_path)
        for groupItem in groupItems["value"]:
            if groupItem['displayName'] == groupName :
                return groupItem['id']

    def get_list_items(self,site_id, list_id, list_limit= 1000) : 

        graph_path = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields&top={list_limit}"
        result = self.get_graph_api(graph_path=graph_path)
        return result["value"]

    def get_user_id_by_email(self, email):
        graph_path = f"https://graph.microsoft.com/v1.0/users/{email}"
        graph_data = self.get_graph_api(graph_path)
        
        return graph_data['id']


class group_permission_graph_api(microsoft_graph_api):

    smart_property_group_id = '4dcb61f6-2134-4665-a329-2aeb511e78f6'
    smart_hq_ops_group_id ='33d4ddad-8383-41ee-9116-c45e5d19e261'
    smart_hq_accts_group_id ='39fc0be9-44c9-48af-9ccf-7b8ea4015d08'
    smart_hq_hoto_group_id ='b036853b-eee5-4111-861c-4c1300c6079a'
    smart_hq_group_id ='c14b0fdb-c827-4761-99ef-1275f7b9188f'
    smart_hq_manager_director_group_id ='d371713c-68c9-44c1-9ae7-d2ff3ed5ed21'

    def get_all_child_users_project(self, user_id, project_list=[]):
        new_project_list = [project_mcst.PRINTER_CODE for project_mcst in User.query.get(user_id).project_list]
        project_list.extend(new_project_list)
        Select_user = User.query.get(user_id)
        subordinate_users = User.query.filter_by(ManagerIncharge = Select_user.employee_id).all()
        for subordinate_user in subordinate_users:
            self.get_all_child_users_project(subordinate_user.id, project_list)

    def get_mcst_folder_id(self, mcst_no):
        initial_folder_graph = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{self.list_id}/drive/root/children"
        graph_data = self.get_graph_api(initial_folder_graph)
        for project_folder in graph_data['value']:
            if not re.search(r"(\d+)\s" , project_folder['name']) :
                return None
            if int(re.search(r"(\d+)\s" , project_folder['name']).group(1) ) == int(mcst_no):
                return project_folder['id']

    def get_folder_permission_user (self, mcst_folder, user_id):
        mcst_detail = smart_project_listing.query.get(mcst_folder)
        user_detail = User.query.get(user_id)
        folder_id = mcst_detail.SHAREPOINT_ID
        graph_user_path = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{self.list_id}/drive/items/{folder_id}/permissions"
        graph_users = self.get_graph_api(graph_user_path)
        try:
            for graph_user in graph_users['value']:
                if not 'email' in  graph_user['grantedTo']['user']:
                    continue
                if graph_user['grantedTo']['user']['email'] == user_detail.email:
                    return graph_user
        except:
            return

    def add_folder_permission_user (self, mcst_folder, user_id):
        mcst_detail = smart_project_listing.query.get(mcst_folder)
        user_detail = User.query.get(user_id)
        folder_id = mcst_detail.SHAREPOINT_ID
        if folder_id == None :
            print (f'{mcst_folder} not found')
            folder_id = self.get_mcst_folder_id(mcst_folder)
            mcst_detail.SHAREPOINT_ID = folder_id
            db.session.commit()
        json_required = {
            "RequireSignIn": "True",
            "SendInvitation": "False",
            "roles": ["write"],
            "recipients": [{"email":f'{user_detail.email}'}],
            "message": "string"
        }
        graph_path = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{self.list_id}/drive/items/{folder_id}/invite"
        graph_data = self.post_graph_api(graph_path,json_required=json_required)
        if not 'value' in graph_data:
            pass
        return graph_data

    def delete_folder_permission_user(self, mcst_folder, user_id):
        mcst_detail = smart_project_listing.query.get(mcst_folder)
        folder_id = mcst_detail.SHAREPOINT_ID
        permission_id = self.get_folder_permission_user(mcst_folder,user_id)
        if permission_id:
            graph_path = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{self.list_id}/drive/items/{folder_id}/permissions/{permission_id['id']}"
            graph_data = self.delete_graph_api(graph_path)
            return (graph_data)

    def add_all_project (self, user_id):

        Select_user = User.query.get(user_id)
        for project in Select_user.project_list:
            self.add_folder_permission_user(project.PRINTER_CODE,user_id)

    def remove_all_project (self, user_id):

        Select_user =  User.query.get(user_id)
        for project in Select_user.project_list:
            self.delete_folder_permission_user(project.PRINTER_CODE,user_id)

    def add_all_user_to_project(self, mcst_folder):
        mcst_detail = smart_project_listing.query.get(mcst_folder)
        for user in mcst_detail.user_list:
            self.add_folder_permission_user(mcst_folder,user.id)

    def remove_all_user_from_single_project(self, mcst_folder):
        mcst_detail = smart_project_listing.query.get(mcst_folder)
        for user in mcst_detail.user_list:
            self.delete_folder_permission_user(mcst_folder,user.id)

    def get_all_user_info(self):
        graph_path = f"https://graph.microsoft.com/v1.0/users"
        graph_data = self.get_graph_api(graph_path)
        return graph_data['value']
    
    def delete_user(self, user_email,  guest_bool = False):

        user_principal_name = f'{user_email.replace("@","_")}%23EXT%23%40smartpropertysingapore.onmicrosoft.com' if guest_bool else user_email
        graph_path = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}"
        result = self.delete_graph_api(graph_path=graph_path)
        print ('successful delete', result.text, graph_path)

    def add_member_to_group(self, group_id, user_id):
        graph_path = f'https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref'
        odata_id =f'https://graph.microsoft.com/v1.0/directoryObjects/{user_id}'
        json_required = {
            "@odata.id" : odata_id
        }
        join_group_graph_data = self.post_graph_api(graph_path, json_required=json_required)
        return join_group_graph_data

    def add_new_user (self,  displayname , jobTitle=None, businessPhones=None, employeeName=None, employee_id=None, ManagerIncharge=None , guest_bool = False , guest_email = None):
        json_required = {}
        json_required['accountEnabled'] = "true"
        json_required['displayName'] = displayname
        first_name  = displayname.split()[0]
        json_required['mailNickname'] = first_name
        email = f'{guest_email.replace("@","_")}#EXT#@smartpropertysingapore.onmicrosoft.com' if guest_bool else  f'{ ".".join(displayname.split()).lower()}@smartproperty.sg' 
        json_required['userPrincipalName'] = email
        User_password = f'{first_name}$mart{datetime.today().strftime("%d%m")}'
        json_required['passwordProfile'] = { "forceChangePasswordNextSignIn": "false",
                                             "password": User_password
                                             }
        graph_path = f"https://graph.microsoft.com/v1.0/users"
        graph_data = self.post_graph_api(graph_path, json_required=json_required)
        email = f'{guest_email.replace("@","_")}%23EXT%23%40smartpropertysingapore.onmicrosoft.com' if guest_bool else email
        self.amend_user_info(displayname=displayname, email=email, jobTitle=jobTitle, businessPhones=businessPhones,
                                          employee_id=employee_id, guest_email=guest_email)
        
        if guest_bool :
            self.add_member_to_group(group_id=self.site_staff_group_id, user_id=graph_data["id"])

        else:
            self.add_user_license(graph_data['id'])
            if "@" in ManagerIncharge : ManagerIncharge = User.query.filter_by(email=ManagerIncharge).first().employee_id
            if ManagerIncharge: self.put_manager_incharge(email=email, manager_email_id=ManagerIncharge)
            group_permission_list = [self.smart_property_group_id, self.smart_hq_group_id]
            group_permission_list.append(self.smart_hq_accts_group_id if "Accounts" in jobTitle else self.smart_hq_ops_group_id) 
            if any(position in jobTitle for position in ["Director","Manager "]) : group_permission_list.append(self.smart_hq_manager_director_group_id)
            for group_permission in group_permission_list:
                
                self.add_member_to_group(group_id=group_permission, user_id=graph_data["id"])
            
        return graph_data

    def amend_user_info (self,  displayname=None ,email=None, jobTitle=None, businessPhones=None,
     employee_id=None , ManagerIncharge=None, guest_email = None):

        json_required = {}
        if displayname:
            json_required['displayName'] = displayname
            json_required['givenName'] = displayname.split()[0]
            json_required['surname'] = " ".join(displayname.split()[1:])
        # if email: json_required['mail'] = email
        if jobTitle: json_required['jobTitle'] = jobTitle
        if businessPhones: json_required['businessPhones'] = [businessPhones]
        if employee_id: json_required['employeeId'] = employee_id
        if guest_email :
             json_required['mail'] = guest_email
             json_required['userType'] = "Guest"
        json_required['usageLocation'] = "SG"
        graph_path = f"https://graph.microsoft.com/v1.0/users/{email}"
        graph_data = self.patch_graph_api(graph_path,json_required=json_required)
        if ManagerIncharge: self.put_manager_incharge(email=email, manager_email_id=ManagerIncharge)
        # self.db.session.commit()
        
        return graph_data

    def add_user_license(self, user_id):
        graph_path = f"https://graph.microsoft.com/v1.0/users/{user_id}/assignLicense"
        json_required = {
            "addLicenses": [
                {
                    "disabledPlans": [],
                    "skuId": "710779e8-3d4a-4c88-adb9-386c958d1fdf",
                },
                {
                    "disabledPlans": [],
                    "skuId": "a403ebcc-fae0-4ca2-8c8c-7a907fd6c235",
                },
                {
                    "disabledPlans": [],
                    "skuId": "dcb1a3ae-b33f-4487-846a-a640262fadf4",
                },
                {
                    "disabledPlans": [],
                    "skuId": "8c4ce438-32a7-4ac5-91a6-e22ae08d9c8b",
                },
                {
                    "disabledPlans": [],
                    "skuId": "f30db892-07e9-47e9-837c-80727f46fd3d",
                },
            ],
            "removeLicenses":[]}

        graph_data = self.post_graph_api(graph_path, json_required=json_required)
        return graph_data

    def put_manager_incharge(self, email, manager_email_id):
        user_id = self.get_user_id_by_email(email)
        if "@" in manager_email_id :
            manager_id = self.get_user_id_by_email(manager_email_id)
        else:
            manager_user = User.query.filter_by(employee_id=manager_email_id).first()
            manager_id = self.get_user_id_by_email(manager_user.email)

        graph_path = f'https://graph.microsoft.com/v1.0/users/{user_id}/manager/$ref'
        json_required = {
            '@odata.id': f'https://graph.microsoft.com/v1.0/users/{manager_id}'
        }
        
        graph_data = self.put_graph_api(graph_path, json_required=json_required)

        return graph_data

    def get_mcst_list_item (self, mcst_no): 

        mcst_list_items = self.get_list_items(self.smart_hq_site_id, self.smart_property_list_id)
        
        for mcst_list_item in mcst_list_items : 
            if mcst_list_item["fields"]["Title"] == str(mcst_no) : 
                return mcst_list_item

    def update_mcst_list_item (self, mcst_no, fields, list_item_id = None):
        if not list_item_id:
            mcst_list_item = self.get_mcst_list_item(mcst_no)
            list_item_id = mcst_list_item['id']
        data_map_field = {
                'PRINTER_CODE': 'Title',
                'ACCOUNTS_INCHARGE' : 'field_0',
                'PROPERTY_NAME' : 'field_2',
                'START_DATE' : 'field_3',
                'TERMINATED_DATE' : 'field_4',
                'UNITS' : 'field_5',
        }
        graph_field = {data_map_field[key] : value for key, value in fields.items() if key in data_map_field }
        graph_path = f"https://graph.microsoft.com/v1.0/sites/{self.smart_hq_site_id}/lists/{self.smart_property_list_id}" \
                     f"/items/{list_item_id}/fields"
        result = self.patch_graph_api(graph_path=graph_path, json_required=graph_field)         
        return result            
    
    def add_mcst_list_item(self, mcst_no, fields):
        graph_path = f"https://graph.microsoft.com/v1.0/sites/{self.smart_hq_site_id}/lists/{self.smart_property_list_id}" \
                     f"/items"
        fields['PRINTER_CODE'] = str(mcst_no)
        
        result = self.post_graph_api(graph_path=graph_path, json_required={})
        new_id = result['fields']['id']
        
        result = self.update_mcst_list_item(mcst_no=mcst_no,fields=fields, list_item_id=new_id)         

        return result


class planner_graph_api(microsoft_graph_api):
        
    def get_planner_task_id(self, groupName , plannerName, bucketName=""):
        groupId = self.get_group_id(groupName)
        graph_path = f'https://graph.microsoft.com/v1.0/groups/{groupId}/planner/plans'
        plannerItems = self.get_graph_api(graph_path)

        for plannerItem in plannerItems['value']:
            if plannerItem['title'] == plannerName:
                plannerId = plannerItem['id']
        if bucketName == '':
            bucketId = ''
        else:
            graph_path = f'https://graph.microsoft.com/v1.0/planner/plans/{plannerId}/buckets'
            bucketItems = self.get_graph_api(graph_path)
            for bucketItem in bucketItems['value']:
                if bucketItem['name'] == bucketName :
                    bucketId = bucketItem['id']

        return (plannerId,bucketId)

    def delete_all_planner_task( self, groupName, plannerName, bucketName=""):
        plannerPlanId, plannerBucketId = self.get_planner_task_id(plannerName, plannerName, bucketName)
        graph_path =  f'https://graph.microsoft.com/v1.0/planner/plans/{plannerPlanId}/tasks'
        taskItems = self.get_graph_api(graph_path)

        for taskItem in taskItems['value']:
            if taskItem['bucketId'] == plannerBucketId:
                graph_path= f'https://graph.microsoft.com/v1.0/planner/tasks/{taskItem["id"]}'
                self.headers['If-Match'] = taskItem['@odata.etag']

    def post_new_planner_task( self, plannerName, bucketName ,title, description = "", assignUsers = [], checklistitems=[], assignDate = datetime.today() , dueDate = datetime.now(),
                            checklistitemsStatus=[]):

        plannerPlanId, plannerBucketId = self.get_planner_task_id(plannerName,plannerName,bucketName)

        graph_path = f"https://graph.microsoft.com/v1.0/planner/tasks"
        assignments = {}
        checklist = {}
        if pd.to_datetime(assignDate) >= pd.to_datetime(dueDate):
            assignDate = dueDate
        for assignUser in assignUsers :
            user_detail = User.query.get(assignUser)
            assignments[user_detail.azure_id] = {
                "@odata.type": "#microsoft.graph.plannerAssignment",
                "orderHint": " !"

            }
        checklistSerial = 10000
        if not checklistitemsStatus and checklistitems:
            checklistitemsStatus = ["false"] * len(checklistitems)

        for checklistitem, checklistitemStatus in zip(checklistitems,checklistitemsStatus):
            checklistSerial = random.randint(checklistSerial+1, 99999)
            checklist[checklistSerial] = {"@odata.type": "microsoft.graph.plannerChecklistItem",
                                    "isChecked": "false",
                                    "title": checklistitem,
                                    "isChecked": checklistitemStatus}

        json_required = {
            "planId": plannerPlanId,
            "bucketId": plannerBucketId,
            "title": title,
            "assignments": assignments,
            "startDateTime":f'{pd.to_datetime(assignDate, utc=True).isoformat()}',
            "dueDateTime": f'{pd.to_datetime(dueDate, utc=True).isoformat()}'
                    }
        postTask =  self.post_graph_api(graph_path,json_required)
        graph_path = f'https://graph.microsoft.com/v1.0/planner/tasks/{postTask["id"]}/details'
        detailTask = self.get_graph_api(graph_path)
        self.headers['If-Match']=detailTask['@odata.etag']
        patch_json_required = {
            "description": description,
            "checklist": checklist,
            "previewType": 'checklist'
        }
        self.patch_graph_api(graph_path,patch_json_required)
        detailTask = self.get_graph_api(graph_path)
        return (detailTask)


class folder_graph_api(microsoft_graph_api):

    def create_new_folder(self, site_id, list_id, file_path, folder_name):
        check_folder_graph = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/drive/root:/'
        
        folder_created_path = f'{file_path}/{folder_name}' if folder_name else f'{file_path}'
        path_folders = os.path.normpath(folder_created_path).split(os.sep)
        
        for folder_count in range(len(path_folders)):
            check_folder_count = -folder_count if folder_count > 0 else None    
            check_response = self.get_graph_api(f'{check_folder_graph}{"/".join(path_folders[:check_folder_count])}')
            if not "error" in check_response: break

        if not check_folder_count : return
        
        if check_folder_count == -len(path_folders)+1 :
            root_graph_path = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/drive/items'
            json_required = {
            "name": path_folders[0],
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
            }
            result = self.post_graph_api(graph_path=root_graph_path,json_required=json_required)
            
        for folder_count in reversed(range(-check_folder_count)):
            base_folder_path = f'{check_folder_graph}{"/".join(path_folders[:-folder_count-1])}'
            initial_folder_graph = f'{base_folder_path}:/children'
            json_required = {
            "name": path_folders[-folder_count-1],
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
            }
            result = self.post_graph_api(graph_path=initial_folder_graph,json_required=json_required)
    
    def find_latest_file(self,  site_id, list_id, file_path, search_file_name):
        check_folder_graph = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/drive/root:/{file_path}:/children'
        check_response = self.get_graph_api(check_folder_graph)
        lastest_file_time =datetime(2000,1,31)
        lastest_file_name = None
        if "error" in check_response : return None
        for graph_file in  check_response['value']:
            if search_file_name in graph_file['name']: 
                file_modified_time = datetime.strptime(graph_file['lastModifiedDateTime'], "%Y-%m-%dT%H:%M:%SZ")
                if file_modified_time > lastest_file_time: 
                    lastest_file_name = graph_file["name"]

        return self.get_file(site_id=site_id, list_id=list_id,
                file_path_name= f'{file_path}/{lastest_file_name}') if lastest_file_name else None
    
    def get_files_name_in_folder(self, site_id, list_id, file_path):
        check_folder_graph = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/drive/root:/{file_path}:/children'
        check_response = self.get_graph_api(check_folder_graph)
        if "error" in check_response : return None
        return [graph_file['name'] for graph_file in  check_response['value']]

    def get_file_to_pandas(self, sheet_name=0, header=0, skipfooter=0, csv_type =True, *args, **kwargs):
        result = self.get_file(*args, **kwargs)
        if sheet_name or not csv_type :
            file_pd = pd.read_excel(io.BytesIO(result[1]), encoding="utf-8",sheet_name=sheet_name, header=header, skipfooter=skipfooter)
        else:
            file_pd = pd.read_csv(io.BytesIO(result[1]), encoding="utf-8")
        return file_pd

    def get_lastest_excel_file_to_pandas(self, *args, **kwargs):
        
        file_pd = None
        result = self.find_latest_file(*args, **kwargs)
        if result : file_pd = pd.read_csv(io.BytesIO(result[1]), encoding="utf-8")
        return file_pd

    def upload_new_file(self, site_id, list_id, file_path, file, file_name, file_type=None , file_ext=None):

        if not file_type:
            file_type = file.content_type
            file_ext  = file_type.split('/')[1]

        self.create_new_folder(site_id, list_id, file_path,None)
        graph_path = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/drive/root:/{file_path}/{file_name}.{file_ext}:'
        upload_graph_path= f'{graph_path}/content'
        file_bytes = file.read() if "io" in str(type(file)) else file
        result = self.put_graph_api(graph_path=upload_graph_path, content_type=file_type, json_required=file_bytes)
        
        # if true:
        if not result.text :
            session_graph_path = f'{graph_path}/createUploadSession'
            file_size = len(file_bytes)
            json_required ={
                    "@microsoft.graph.conflictBehavior": "replace",
                    # "description": "description",
                    "fileSize": file_size,
                    "name":  file_name 
                   
            }
            
            result = self.post_graph_api(graph_path=session_graph_path, json_required= json_required)
            upload_url = result['uploadUrl']
            self.headers["Connection"] = "keep-alive"
            self.headers['Content-Range'] = f'bytes 0-{file_size-1}/{file_size}'
            result = self.put_graph_api(graph_path=upload_url, content_type=file_type, json_required=file_bytes)

        return [result.json(), f'{file_name}.{file_ext}', file_path]
    
    def get_file(self, site_id, list_id, file_path_name):
        graph_path = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/drive/root:/{file_path_name}:/content'
        file = self.get_graph_api(graph_path, jsonify_bool=False)
        file_ext = file_path_name.split('.')[-1]
        file_content_type = f"image/{file_ext}" if "jp" in file_ext else f"application/{file_ext}"
        return [file,file.content, file_content_type]

    def create_mcst_new_folder(self, mcst_no, file_path, folder_name):
        
        mcst_detail = smart_project_listing.query.get(mcst_no)
        self.create_new_folder (self.site_id, self.list_id, f'{mcst_no:04d} - {mcst_detail.PROPERTY_NAME}/{file_path}', folder_name)
        

class mcst_template_header(folder_graph_api):

    def get_template_header(self, mcst_no):
        mcst_obj = smart_project_listing.query.get(mcst_no)
        file_path_name = f"TEMPLATE\ESTATE LETTERHEAD\IMAGE HEADER\{mcst_no:04d}_{mcst_obj.PROPERTY_NAME}.png"
        header_image = self.get_file(site_id=self.site_id, list_id= self.list_id,file_path_name=file_path_name)
        
        return header_image


class teams_chat_graph_api(microsoft_graph_api):
    new_user_chat_group_id = '19:18a964df11ff4849a88c340ad5b26e26@thread.v2'
    new_project_chat_group_id = '19:9153f667e4104d8da2efe13f7975ef13@thread.v2'
    remove_project_chat_group_id = '19:d391a5cdb2d742bba14cf2f30fab4ff0@thread.v2'


    def create_chat(self, user_email):
        user_id = self.get_user_id_by_email(user_email)
        active_user_id =self.get_user_id_by_email(self.active_user)
        graph_path = f'https://graph.microsoft.com/beta/chats'
        json_required = {'chatType': 'oneOnOne',
                        'members': [
                    {
                    '@odata.type': '#microsoft.graph.aadUserConversationMember',
                    'roles': ['owner'],
                    'user@odata.bind': f'https://graph.microsoft.com/beta/users(\'{user_id}\')'
                    },
                    {
                    '@odata.type': '#microsoft.graph.aadUserConversationMember',
                    'roles': ['owner'],
                    'user@odata.bind': f'https://graph.microsoft.com/beta/users(\'{active_user_id}\')'
                    }
                ]
                }
        result = self.post_graph_api(graph_path= graph_path, json_required=json_required)
        return result
 
    def send_message(self, user_email, message_body): 

        create_chat_result = self.create_chat(user_email=user_email)
        graph_path = f'https://graph.microsoft.com/beta/chats/{create_chat_result["id"]}/messages'
        result = self.post_graph_api(graph_path=graph_path, json_required={"body":{"content": message_body}})
        return result
    
    def send_group_message(self, group_message_id, message_body): 

        graph_path = f'https://graph.microsoft.com/beta/chats/{group_message_id}/messages'
        result = self.post_graph_api(graph_path=graph_path, 
        json_required={"body":{"contentType":"html",
                            "content": message_body}})
        return result