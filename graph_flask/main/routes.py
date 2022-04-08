import os
import re
import uuid
from datetime import date
from datetime import datetime
from flask import Blueprint, render_template,request, redirect,url_for, session
from flask.helpers import make_response
from sqlalchemy import null, true
from flask_mail import Message
from graph_flask import mail
from graph_flask.microsoft.utils import  require_microsoft_login, _build_auth_url
from graph_flask.microsoft.utils import _get_token_from_cache ,_build_msal_app, _save_cache,_load_cache, microsoft_graph_api
from graph_flask.microsoft.utils import folder_graph_api, group_permission_graph_api, teams_chat_graph_api
from graph_flask.models import add_attendance_participant_register, form_question_records_details, form_sub_category, job_title_role, site_staff, smart_project_listing,User,db
from graph_flask.models import user_project, stationary_type, stationary_usage, form_register,form_question_records_details
from graph_flask.models import form_template, form_question_records, function_list, stationary_topup
from graph_flask.models import Role, Job_title_role_relationship, attendance_register
from graph_flask.main.utils import getMcstDetails, getMcstGstReg, jsonify_api_headers, update_sql_json
from graph_flask.function_module.utils import invoicepaynowGenerate, printing_postage_report_generate
from graph_flask.ar_module.utils import ar_graph_api
from flask_cors import cross_origin
from cryptography.fernet import Fernet
import graph_flask.config as config
import json
main = Blueprint('main', __name__)


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # enable non-HTTPS for testing
# session = requests.session()


@main.route('/')
@cross_origin(supports_credentials=True)
def homepage():
    """Render the home page."""

    return redirect(url_for('main.main_dashboard'))

@main.route("/login")
# @cross_origin(supports_credentials=True)
def login():
    session["state"] = str(uuid.uuid4())
    session['redirectPage'] = request.headers.get("Referer")
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    auth_url = _build_auth_url(scopes=config.SCOPE, state=session["state"])
    return redirect(auth_url)

@main.route("/logout")
@cross_origin(supports_credentials=True)
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("main.homepage", _external=True))

@main.route("/api/mcstList")
@require_microsoft_login
@cross_origin(supports_credentials=True)
def mcstList():
    request_data = json.loads(request.data)

    userData = smart_project_listing.query.all()
    return userData

@main.route(config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
@cross_origin(supports_credentials=True)
def authorized():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("main.homepage"))  # No-OP. Goes back to Index page
    if "error" in request.args:  # Authentication/Authorization failure
        return render_template("auth_error.html", result=request.args)
    if request.args.get('code'):
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args['code'],
            scopes=config.SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=url_for("main.authorized", _external=True))
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    return redirect(session['redirectPage'] )

@main.route("/api/testing")
# @require_microsoft_login
def apitest():
    template_html = open(r"graph_flask/templates/email/OBC_invitation.html",'r').read()
    # email_list =[]
    crpyter = Fernet(os.environ.get('mcst_key'))
    attendance_id = crpyter.encrypt(str(1).encode('utf-8')).decode('utf-8')    
    msg = Message( recipients=["clarence.yeo@smartproperty.sg"], sender="administrator@smartproperty.sg"
    )    
    msg.subject = f'OUTCOME-BASED CONTRACTING (OBC) FOR SECURITY SERVICES WEBINAR'
    for project_item in smart_project_listing.query.filter(smart_project_listing.TERMINATED_DATE >= date.today()).all():
        for site_staff_item in project_item.site_staff_list:
            print (site_staff_item)
            email_encrypt = crpyter.encrypt(site_staff_item.site_email.encode('utf-8')).decode('utf-8')    
            url_link = f'https://smartsgportal.azurewebsites.net/#/public/attendancechecklist/{attendance_id}/{email_encrypt}'
            msg.html = template_html.replace("***url***", url_link)
            # mail.send(msg)
        break
    for user_item in User.query.join(job_title_role).filter(User.termination_date == None, job_title_role.Department == "Operations").all():
            print (user_item)
            email_encrypt = crpyter.encrypt(user_item.email.encode('utf-8')).decode('utf-8')    
            url_link = f'https://smartsgportal.azurewebsites.net/#/public/attendancechecklist/{attendance_id}/{email_encrypt}'

    # testing = microsoft_graph_api()
    # result = testing.get_user_id_by_email("clarence.yeo@smartproperty.sg")
    return {}

@main.route("/main_dashboard")
@require_microsoft_login
@cross_origin(supports_credentials=True)
def main_dashboard():
    # if Pending_form.is_submitted():
    #     if Pending_form.File_uploaded.data == None:
    #         flash('No file is selected, click choose file to upload file', 'danger')
    #     else:
    #         extension = os.path.splitext(Pending_form.File_uploaded.data.filename)[1]
    #         filename = f'{datetime.today().strftime("%Y%m%d")}_{Pending_form.Mcst_no.data}_' \
    #                    f'{Pending_form.pending_item.data}{extension}'
    #         server_connection().save_file(Pending_form.save_path.data , filename,
    #                                       Pending_form.File_uploaded.data.read())
    #
    #         mcst_os = mcst_os_list.query.get_or_404(Pending_form.item_id.data)
    #
    #         mcst_os.File_uploaded = os.path.join(mcst_os.File_uploaded, filename).replace('\\','/')
    #
    #         mcst_os.Date_received = datetime.now()
    #         db.session.commit()
    #
    #         flash(f'{filename} had been uploaded' , 'success')
    #     # redirect(url_for('main.main_dashboard'))
    #


    # Mcst_pending_items = mcst_os_list.query.join(smart_project_listing).filter(smart_project_listing.ACCOUNTS_INCHARGE == active_username).\
    #     filter(mcst_os_list.Date_received == "").order_by(mcst_os_list.MCST_no).all()

    # profile_pic=  url_for('static', filename= 'profile_pics/' + current_user.image_file)
    # Mcst_pending_items= MCST_pending_list.query.filter(MCST_pending_list.File_uploaded == '').order_by(MCST_pending_list.MCST_id).all()
    return render_template('Main_dashboard.html', title='main_dashboard')

@main.route("/api/jobtitlelist", methods=['GET'])
@require_microsoft_login
def jobtitlelist():
    
    return jsonify_api_headers([job_title.to_json() for job_title in job_title_role.query.all()])
    
@main.route("/api/jobtitlerolelist", methods=['POST'])
@require_microsoft_login
def jobtitlerolelist():
    
    request_data = json.loads(request.data)
    selected_role_name = request_data['selected_role']
    selected_role = Role.query.filter_by(name=selected_role_name).first()
    return jsonify_api_headers([job_title.to_json() for job_title in selected_role.job_title_list])

@main.route("/api/updatejobtitlerole", methods=['POST'])
@require_microsoft_login
def updatejobtitlerole():
    
    request_data = json.loads(request.data)
    role_permission , selected_role_name , selected_job_title = request_data['role_permission'] , request_data['selected_role_name'] , request_data['selected_job_title']
    selected_role_id = Role.query.filter_by(name = selected_role_name).first().id
    if role_permission =="NO" : 
            job_title_relationship = Job_title_role_relationship.query.filter_by(job_title=selected_job_title, role_id= selected_role_id )
            job_title_relationship.delete()
    else: 
        job_title_relationship= Job_title_role_relationship(job_title=selected_job_title, role_id= selected_role_id)
        db.session.add(job_title_relationship)
    
    db.session.commit()

    return jsonify_api_headers({'result': "item updated" })

@main.route("/api/userrole", methods=['GET','POST'])
@require_microsoft_login
def userrole():

    request_data = json.loads(request.data)
    user_email = request_data['user_email']
    user_roles = User.query.filter_by(email=user_email).first().jobTitleDetails.role_list
    
    return jsonify_api_headers([role_item.name for role_item in user_roles])

@main.route("/api/projectlist", methods=['GET','POST'])
@require_microsoft_login
def apiProjectList():
    if request.data : 
        request_data = json.loads(request.data)
        user_email = request_data['user_email']
        project_list = User.query.filter_by(email=user_email).first().project_list
    else :
        project_list =  smart_project_listing.query.all()
    return jsonify_api_headers([project.to_json() for project in project_list])

@main.route("/api/projectusercount", methods=['GET'])
@require_microsoft_login
def projectusercount():
    
    return jsonify_api_headers([project.user_count_json() for project in smart_project_listing.query.all()])

@main.route("/api/projectinfo", methods=['GET','POST'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def apiprojectinfo():
    request_data = json.loads(request.data)
    enquire_project = smart_project_listing.query.filter_by(PRINTER_CODE = int(request_data['id'])).first()
    return jsonify_api_headers(enquire_project.to_info_json())

@main.route("/api/newprojectinforetreive", methods=['GET','POST'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def newprojectinforetreive():
    # for project in smart_project_listing.query.all():
    
    request_data = json.loads(request.data)
    enquire_project = getMcstDetails(int(request_data['id']))
    enquire_json ={

                'PROPERTY_NAME': enquire_project['usr_devtname'].upper(),
                'START_DATE': datetime.today(),
                'PREVIOUS_MA': enquire_project['managementname'],
                'TERMINATED_DATE': '31/12/2199',
                'NEW_MA': '',
                'UNITS': enquire_project['mcst_stratalota'],
                'BILLINGS_CYCLE': '',
                'ROAD_NAME_ADDRESS': enquire_project['mcst_roadname'],
                'OFFICIAL_ADDRESS': enquire_project['devt_location'],
                'MAILING_ADDRESS': '',
                'UEN_NO': enquire_project['sub_mcstuen'],
        }


    return jsonify_api_headers(enquire_json)

@main.route("/api/projectinfoupdate", methods=['POST'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def apiprojectinfoupdate():
    
    newProject = False
    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    graph_fields ={}
    enquire_project = smart_project_listing.query.filter_by(PRINTER_CODE = int(request_data['id'])).first()
    microsoft_api = group_permission_graph_api()

    if not enquire_project:
        enquire_project = smart_project_listing(PRINTER_CODE=int(request_data['id']), MCST_no=int(request_data['id']))
        newProject = True

    for data_item in request_value:

        if hasattr(enquire_project, data_item) and type(request_value[data_item]) == str:
            enquire_project.__setattr__(data_item, datetime.strptime(request_value[data_item],
                                                                     "%d/%m/%Y") if "DATE" in data_item else
            request_value[data_item])
            graph_fields[data_item] = datetime.strptime(request_value[data_item],
            "%d/%m/%Y").isoformat() if "DATE" in data_item else request_value[data_item]

    if newProject:
         db.session.add(enquire_project)
         microsoft_api.add_mcst_list_item(request_data['id'], fields=graph_fields)
         folder_graph = folder_graph_api()
         folder_graph.create_mcst_new_folder(mcst_no=int(request_data['id']), 
         file_path='BILLING', folder_name='BILLING INVOICES')
         message_graph_api = teams_chat_graph_api()
         message_body = f'This is an automated message : <br>' \
                        f'New MCST Project <br>' \
                        f'Mcst : {enquire_project.PRINTER_CODE} <br>'\
                        f'Property name: {enquire_project.PROPERTY_NAME} <br>'\
                        f'Start Date : {enquire_project.START_DATE.strftime("%d-%m-%Y")} <br>'\
                        f'Previous Ma : {enquire_project.PREVIOUS_MA if enquire_project.PREVIOUS_MA else "TBA"} <br>'\
                        
         message_graph_api.send_group_message(group_message_id=message_graph_api.new_project_chat_group_id, message_body=message_body)
    else:
        if enquire_project.TERMINATED_DATE <= datetime(2099,12,31) : 
            message_graph_api = teams_chat_graph_api()
            message_body = f'This is an automated message : <br>' \
                        f'Terminated Project <br>' \
                        f'Mcst : {enquire_project.PRINTER_CODE} <br>'\
                        f'Property name: {enquire_project.PROPERTY_NAME} <br>'\
                        f'Terminated Date : {enquire_project.TERMINATED_DATE.strftime("%d-%m-%Y")} <br>'\
                        f'New Ma : {enquire_project.NEW_MA if enquire_project.NEW_MA else "TBA"} <br>'\
                        f'Ops In Charge: {enquire_project.operations_in_charge} <br>'\
                        f'Accts In Charge: {enquire_project.accounts_in_charge}'
            message_graph_api.send_group_message(group_message_id=message_graph_api.remove_project_chat_group_id, message_body=message_body)
        
        microsoft_api.update_mcst_list_item(request_data['id'], graph_fields)
    db.session.commit()



    return {"response" : "successful"}

@main.route("/api/projectremoveuser", methods=['DELETE'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def projectremoveuser():

    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    if request_value.get('mcst_no'):
        selected_user = site_staff.query.get(request_value['id'])
        if selected_user.site_email : 
            graph_api = group_permission_graph_api()
            graph_api.delete_user(selected_user.site_email , guest_bool=true)
        db.session.delete(selected_user)

    else:
        selected_user = User.query.filter_by(displayname= request_value['displayname']).first()
        mcst_no = request_data['id']
        microsoft_api = group_permission_graph_api()
        if "accounts" in selected_user.jobTitle.lower():
            fields = {
            'field_0' : ""
            }
            microsoft_api.update_mcst_list_item(mcst_no, fields) 

        for user in selected_user.get_all_child_users():
            microsoft_api.delete_folder_permission_user(mcst_no,user.id)
        user_project_entry = user_project.query.filter_by(user_id=selected_user.employee_id,
                                                        project_id=request_data['id']).first()
        db.session.delete(user_project_entry)
    
    db.session.commit()
    return jsonify_api_headers({'result':'user remove successfully'})

@main.route("/api/projectadduser", methods=['POST'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def projectadduser():

    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    mcst_no = request_data['id']
    selected_user = User.query.filter_by(displayname= request_value['displayname']).first()
    microsoft_api = group_permission_graph_api()
    if "accounts" in selected_user.jobTitle.lower():
        fields = {
        'ACCOUNTS_INCHARGE' : selected_user.displayname
        }
        microsoft_api.update_mcst_list_item(mcst_no, fields) 

    else:
        for user in selected_user.get_all_child_users(): microsoft_api.add_folder_permission_user(request_data['id'],
                                                                                               user.id)
    user_project_entry = user_project(user_id=selected_user.employee_id,
                                                      project_id=mcst_no)
    db.session.add(user_project_entry)
    db.session.commit()
    return jsonify_api_headers({'result':'user added successfully'})

@main.route("/api/addsitestaffuser", methods=['POST'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def addsitestaffuser():

    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    site_staff_id = request_data.get('id')
    email_exist = site_staff.query.filter_by(site_email = request_value.get('site_email')).all()
    if site_staff_id :
        site_staff_obj = site_staff.query.get(site_staff_id) 
        delete_user_email = site_staff_obj.site_email if not site_staff_obj.site_email == request_value.get('site_email')  else None
        
    else:
        site_staff_obj= site_staff()
        db.session.add(site_staff_obj)
        delete_user_email =None
    update_sql_json(sql_object=site_staff_obj, request_value=request_value)
    db.session.commit()
    if request_value.get('site_email') :
        
        if not email_exist:
            graph_api = group_permission_graph_api()
            displayname = f'{site_staff_obj.mcst_no:04d} - {site_staff_obj.projectDetails.PROPERTY_NAME} - {site_staff_obj.jobTitleDetails.jobTitle_shortform}'
            graph_api.add_new_user(displayname= displayname, jobTitle= site_staff_obj.job_title_name, businessPhones=site_staff_obj.site_contact, 
            guest_bool=True, guest_email=site_staff_obj.site_email)

        
        if delete_user_email: graph_api.delete_user(delete_user_email, guest_bool=true)
        
    return jsonify_api_headers({'result':'user added successfully'})

@main.route("/api/adduser", methods=['POST'])
@require_microsoft_login
@cross_origin(supports_credentials=True)
def adduser():

    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    
    # user_mobile_no = request_value.get('mobile_contact')
    # user_hq_direct_ext = request_value.get('office_contact')
    request_value['mobile_no'] = request_value.get('mobile_contact')
    request_value['hq_direct_ext'] = request_value.get('office_contact')
    if request_value.get('ManagerIncharge') :
         ManagerIncharge_emp_id = User.query.filter_by(displayname= request_value['ManagerIncharge']).first().employee_id
         request_value['ManagerIncharge'] = ManagerIncharge_emp_id
        
    user_id = request_value.get('id')
    
    if user_id :
        user_obj = User.query.get(user_id) 
        check_fields =  ['displayname', 'employee_id', 'jobTitle', 'employeeName','mobile_no','ManagerIncharge']
        for check_field in check_fields:
            if not user_obj.__getattribute__(check_field) == request_value[check_field]: 
                graph_api = group_permission_graph_api()        
                graph_api.amend_user_info(displayname= request_value.get('displayname'),
                jobTitle= request_value.get('jobTitle'), businessPhones=request_value.get('mobile_no'),
                employee_id=request_value.get('employee_id'), 
                email= request_value.get('email'),
                ManagerIncharge=request_value.get('ManagerIncharge'))
                break
        
        update_manager_folder = true if not user_obj.ManagerIncharge == request_value['ManagerIncharge'] else False
            
        if not user_obj.employee_id == request_value['employee_id']:
            userlist = User.query.filter_by(ManagerIncharge = user_obj.employee_id).all()
            for userobj in userlist : 
                userobj.ManagerIncharge =  request_value['employee_id']
        update_sql_json(sql_object=user_obj, request_value=request_value)
        
        if update_manager_folder: 
            # graph_api = group_permission_graph_api()        
            for user in user_obj.get_all_child_users(): 
                for project in user.projects_list: 
                    graph_api.add_folder_permission_user(project.PRINTER_CODE,user.id)

    
    else:
        user_obj= User()
        update_sql_json(sql_object=user_obj, request_value=request_value)
        db.session.add(user_obj)
        graph_api = group_permission_graph_api()
        graph_api.add_new_user(displayname= request_value.get('displayname'),
         jobTitle= request_value.get('jobTitle'), businessPhones=request_value.get('mobile_contact'),
         employee_id=request_value.get('employee_id'), employeeName=request_value.get('employeeName'), 
         ManagerIncharge=request_value.get('ManagerIncharge'))
        message_graph_api = teams_chat_graph_api()
        message_body = f'This is an automated message : <br>' \
                       f'New user added <br>' \
                       f'Displayname : {user_obj.displayname} <br>'\
                       f'Start Date : {user_obj.start_date.strftime("%d-%m-%Y")} <br>'\
                       f'Email : {user_obj.email} <br>'\
                       f'Job Title : {user_obj.jobTitle} <br>'\
                       f'mobile Contact: {user_obj.mobile_no} <br>' \
                       f'Manager In Charge: {user_obj.manager_display_name()} '
        message_graph_api.send_group_message(group_message_id=message_graph_api.new_user_chat_group_id, message_body=message_body)
    
    
    db.session.commit()

    return jsonify_api_headers({'result':'user added successfully'})

@main.route("/api/userlist", methods=['GET'])
@require_microsoft_login
def userlist():
    
    return jsonify_api_headers([user_obj.to_json() for user_obj in User.query.all()])

@main.route("/api/stationarytype", methods=['GET'])
@require_microsoft_login
def stationarytype():
    
    return jsonify_api_headers([stationary_item.to_json() for stationary_item in stationary_type.query.all()])

@main.route("/api/stationarystock", methods=['POST'])
@require_microsoft_login
def stationarystock():
    request_data = json.loads(request.data)
    request_usage_type_list = json.loads(request_data['value'])
    return jsonify_api_headers([
        stationary_type.query.get(request_usage_type).to_stock_json()
    for request_usage_type in request_usage_type_list])

@main.route("/api/stationaryusagelist", methods=['GET','POST'])
@require_microsoft_login
def stationaryusagelist():

    request_data = json.loads(request.data)
    if request_data.get('mcstNo'):
        mcst_no= json.loads(request_data['mcstNo'])
    else: 
        crpyter = Fernet(os.environ.get('mcst_key'))
        mcst_no = crpyter.decrypt(request_data['mcst_key'].encode('utf-8')).decode('utf-8')
    return jsonify_api_headers([stationary_item.to_json() for 
    stationary_item in stationary_usage.query.filter_by(usage_mcst = mcst_no).
    order_by(stationary_usage.usage_date.desc()).all()])
  
@main.route("/api/addstationaryitem", methods=['POST'])
@require_microsoft_login
def addstationaryitem():
    # for project in smart_project_listing.query.all():
    FALL_BELOW_PERCENTAGE = 0.10

    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    if request_value['data_type'] == "USAGE" : 
        newStationaryEntry = stationary_usage()
        
        update_sql_json(sql_object= newStationaryEntry, request_value=request_value)
        db.session.add(newStationaryEntry)
        db.session.commit()
        stationary_type_obj= stationary_type.query.get(newStationaryEntry.usage_type)
        remain_stock = stationary_type_obj.remain_stock()
        fall_below_amount = stationary_type_obj.last_topup() * FALL_BELOW_PERCENTAGE
        
        if type(remain_stock) == float:
            if remain_stock < fall_below_amount : 
                teams_graph = teams_chat_graph_api()
                message_body = f'Auto Message : Stationary {newStationaryEntry.stationary_details.item_group} - ' \
                            f'{newStationaryEntry.stationary_details.item_type}' \
                            f'is running low on stock (current stock - {remain_stock})'    
                teams_graph.send_message('hq.admin@smartproperty.sg', message_body)
    elif request_value['data_type'] == "TOPUP" : 
        newStationaryEntry = stationary_topup()
        request_value['topup_date'] = request_value.pop('usage_date')
        request_value['topup_quantity'] = request_value.pop('usage_quantity')
        update_sql_json(sql_object=newStationaryEntry, request_value=request_value)
        db.session.add(newStationaryEntry)
        db.session.commit()

    return jsonify_api_headers({'response':"succssful added"})

@main.route("/api/checklistrecords", methods=['GET'])
@require_microsoft_login
def checklistrecords():
    return jsonify_api_headers([register.to_json() for register in form_register.query.all()])

@main.route("/api/checklistrecordsdetail", methods=['POST'])
@require_microsoft_login
def checklistrecordsdetail():
    request_data = json.loads(request.data)
    request_id = json.loads(request_data['id'])
    checklist_id = json.loads(request_data['checklist_id'])
    record_list = ([record_detail.to_json() for record_detail in
     form_question_records.query.filter_by(question_id=request_id,
      form_register_id=checklist_id).first().records_details])
    return jsonify_api_headers(record_list)

@main.route("/api/amendchecklistdetailentry", methods=['POST'])
@require_microsoft_login
def amendchecklistdetailentry():
    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    request_id = json.loads(request_data['id'])
    form_qn_record = form_question_records_details.query.get(request_id['id'])
    if not form_qn_record: 
        record_id = form_question_records.query.filter_by(
            form_register_id =request_id['form_register_id'],
            question_id =request_id['question_record_id']
        ).first().id
        form_qn_record= form_question_records_details(
        form_question_records_id = record_id)
        db.session.add(form_qn_record)
    update_sql_json(form_qn_record, request_value)
    db.session.commit()

    return jsonify_api_headers({'id':form_qn_record.id})

@main.route("/api/uploadchecklistimage", methods=['POST'])
@require_microsoft_login
def uploadchecklistimage():
    request_image = request.files.get('image')
    request_id = request.form.get('id')
    form_qn_record = form_question_records_details.query.get(request_id)
    folder_graph = folder_graph_api()
    folder_path = form_qn_record.save_path()
    _, file_name_ext = folder_graph.upload_new_file(folder_graph.smart_hq_site_id, folder_graph.checklist_list_id,folder_path,
    request_image,f'{form_qn_record.id:03d}')
    form_qn_record.image_attached_file = f'{folder_path}/{file_name_ext}'
    db.session.commit()

    return jsonify_api_headers({'image_attached_file':form_qn_record.image_attached_file})

@main.route("/api/getchecklistimage", methods=['POST'])
@require_microsoft_login
def getchecklistimage():
    request_data = json.loads(request.data)
    request_id = request_data['id']
    form_qn_record = form_question_records_details.query.get(request_id)
    folder_graph = folder_graph_api()
    _, image_file_content, file_content_type = folder_graph.get_file(folder_graph.smart_hq_site_id, folder_graph.checklist_list_id,
    form_qn_record.image_attached_file)
    response = make_response(image_file_content)
    response.headers.set('Content-Type', file_content_type)
    return response

@main.route("/api/newchecklistrecord", methods=['POST'])
@require_microsoft_login
def newchecklistrecord():
    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    new_checklist_record = form_register()
    for data_item in request_value:
        if hasattr(new_checklist_record, data_item) and type(request_value[data_item]) in [str, int, float] :
            new_checklist_record.__setattr__(data_item, datetime.strptime(request_value[data_item],"%Y-%m-%dT%H:%M:%S.%fZ") 
            if "DATE" in data_item.upper() else request_value[data_item])
    db.session.add(new_checklist_record)
    db.session.commit()            

    return jsonify_api_headers({'id':new_checklist_record.id})

@main.route("/api/checklisttype", methods=['GET'])
@require_microsoft_login
def checklisttype():
    return jsonify_api_headers([template.to_json() for template in form_template.query.all()])

@main.route("/api/checklistquestions", methods=['POST'])
@require_microsoft_login
def checklistquestions():
    request_data = json.loads(request.data)
    request_id = json.loads(request_data['id'])
    form_template_selected = form_register.query.get(request_id).form_info
    return jsonify_api_headers([qn.to_json_with_records(request_id) for sub_category in 
    form_template_selected.form_sub_category for qn in sub_category.form_question])

@main.route("/api/checklistregister", methods=['POST'])
@require_microsoft_login
def checklistregister():
    request_data = json.loads(request.data)
    request_id = json.loads(request_data['id'])
    form_register_selected = form_register.query.get(request_id)
    return jsonify_api_headers(form_register_selected.to_json())

@main.route("/api/amendchecklistanswer", methods=['POST'])
@require_microsoft_login
def amendchecklistanswer():
    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    form_qn_record = form_question_records.query.filter(
        form_question_records.form_register_id ==request_value['form_register_id'] ,
        form_question_records.question_id ==request_value['question_id'] 
        ).first()
    if not form_qn_record: 
        form_qn_record= form_question_records(
        form_register_id =request_value['form_register_id'],
        question_id =request_value['question_id']
    )
        db.session.add(form_qn_record)
    update_sql_json(form_qn_record, request_value)
    form_register_selected = form_register.query.get(request_value['form_register_id'])
    form_register_selected.last_modified_date = form_qn_record.date_of_record
    form_register_selected.last_modified_by = form_qn_record.modified_by

    db.session.commit()
    return {'response':'updated completed'}

@main.route("/api/attendancerecords", methods=['POST'])
@require_microsoft_login
def attendancerecords():
    request_data = json.loads(request.data)
    request_id = request_data['id']
    user_email_encrypt = request_data['email']
    crpyter = Fernet(os.environ.get('mcst_key'))
    meeting_id = crpyter.decrypt(request_id.encode('utf-8')).decode('utf-8')
    user_email = crpyter.decrypt(user_email_encrypt.encode('utf-8')).decode('utf-8')
    
    site_staff_id = site_staff.query.filter(site_staff.site_email == user_email).first().id
    attendance_register_selected = attendance_register.query.filter(attendance_register.meeting_id == meeting_id ,
    attendance_register.hq_user_email == user_email).first() if "smartproperty.sg" in user_email else attendance_register.query.filter(attendance_register.meeting_id == meeting_id ,
    attendance_register.site_staff_id == site_staff_id).first()
    if not attendance_register_selected : 
        if "smartproperty.sg" in user_email: 
            attendance_register_selected= attendance_register(meeting_id= meeting_id, hq_user_email=user_email)
        else: 
            attendance_register_selected= attendance_register(meeting_id= meeting_id, site_staff_id=site_staff_id)
        db.session.add(attendance_register_selected)
        db.session.commit()
    return jsonify_api_headers(attendance_register_selected.to_json())

@main.route("/api/amendattendancerecords", methods=['POST'])
@require_microsoft_login
def amendattendancerecords():
    # crpyter = Fernet(os.environ.get('mcst_key'))
    request_data = json.loads(request.data)
    request_value = json.loads(request_data['value'])
    # request_id = request_data['id']
    # user_email_encrypt = request_data['email']
    # meeting_id = crpyter.decrypt(request_id.encode('utf-8')).decode('utf-8')
    # user_email = crpyter.decrypt(user_email_encrypt.encode('utf-8')).decode('utf-8')
    form_qn_record = attendance_register.query.get(request_value['id'])
    update_sql_json(form_qn_record, request_value)
    form_qn_record.locked = True
    new_participant_id = []
    for add_participant in request_value['additional_participants']:
        
        if not type(add_participant['id']) == int : 
            add_participant_obj= add_attendance_participant_register(attendance_register_id=request_value['id'])
            db.session.add(add_participant_obj)
            add_participant.pop('id')
        else : 
            add_participant_obj = add_attendance_participant_register.query.get(add_participant['id'])
        update_sql_json(add_participant_obj, add_participant)
        db.session.commit()
        new_participant_id.append(add_participant_obj.id)
    existing_id_list = [additional_participants.id for additional_participants in form_qn_record.additional_participants if not additional_participants.id in new_participant_id ]
    print (existing_id_list, new_participant_id)
    for existing_id in existing_id_list :
        delete_entry = add_attendance_participant_register.query.get(existing_id)
        db.session.delete(delete_entry)
    

    db.session.commit()
    return {'response':'updated completed'}


@main.route("/api/functionlist", methods=['GET'])
@require_microsoft_login
def functionlist():
    return jsonify_api_headers([function_item.to_json() for function_item in function_list.query.all()])

@main.route("/api/functiongenerate", methods=['POST'])
@require_microsoft_login
def functiongenerate():
    request_id = request.form.get('id')
    if request_id == "1" :
        # paynow invoice genearate
        request_file = request.files.get('file')
        result = invoicepaynowGenerate(request_file)
    elif request_id == "2" : 
        request_data = json.loads(request.form.get('data'))
        report_month = request_data['monthdate']
        result = printing_postage_report_generate(report_month=report_month)
    return  jsonify_api_headers(result)

    
