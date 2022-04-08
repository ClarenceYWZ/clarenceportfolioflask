import os
from flask import Blueprint, render_template,request, flash,redirect, url_for

import requests

import graph_flask.config as config
ar_module = Blueprint('ar_module', __name__)


#
#
#
# @ar_module.route("/ar_module_strata_upload" , methods=['GET', 'POST'])
# @require_microsoft_login
# def ar_module_strata_upload():
#     Pending_form = ar_module_list_form()
#
#
#     # print (active_site.SITE_EMAIL)
#     if Pending_form.is_submitted():
#         if Pending_form.File_uploaded.data == None:
#             flash('No file is selected, click choose file to upload file', 'danger')
#         else:
#             # r"C:\Users\Clarence Yeo\OneDrive - Smart Property Management (S) Pte Ltd\PRESENTATION\VIRTUAL ar_module\VIRTUAL ar_module ATTENDANCE LIST.xlsx"
#             print (Pending_form.File_uploaded)
#
#
#             extension = os.path.splitext(Pending_form.File_uploaded.data.filename)[1]
#             filename = f'{datetime.today().strftime("%Y%m%d")}_{Pending_form.Mcst_no.data}_' \
#                        f'{Pending_form.pending_item.data}{extension}'
#
#
#     return render_template('ar_module/ar_module_file_upload.html', Pending_form= Pending_form)
#
#
# @ar_module.route("/ar_module_instruction_email" , methods=['GET', 'POST'])
# def ar_module_instruction_email():
#     if request.method == "POST":
#         strata_spreadsheet = request.files['File_uploaded']
#         email_sent = send_ar_module_instruction_email(strata_spreadsheet)
#         return (email_sent)
#
#
#
#
# @ar_module.route("/globino/delete_all")
# def globino_deleteall():
#     for userid in range(39286,39394):
#         globino_delete_user(userid)
#
#
#
# @ar_module.route("/ar_moduleform/<int:mcst_no>/<int:form_id>/<int:user_id>", methods=['GET', 'POST'])
# def form(mcst_no,form_id,user_id):
#     form_entry=  form_register.query.filter(form_register.form_id == form_id).\
#         filter(form_register.MCST_id == mcst_no).filter(form_register.form_open == True).first()
#     if not form_entry:
#         flash('the form does not exist or close', 'danger')
#         return redirect(url_for('main.login'))
#
#
#     form =  sample_form()
#
#     mcst_info = smart_project_listing.query.filter(smart_project_listing.PRINTER_CODE == mcst_no).first()
#     user_info = strata_roll.query.filter(strata_roll.ar_module_id == user_id).first()
#     print (user_info)
#     own_units = strata_roll.query.filter(strata_roll.subsidiary_proprietors == user_info.subsidiary_proprietors).filter(strata_roll.ar_module_id != user_id)
#     available_units = strata_roll.query.filter(strata_roll.MCST_id== user_info.MCST_id).filter(strata_roll.ar_module_id != user_id)
#
#     estate_logo = url_for('static', filename= 'img/SMART LOGO.png')
#     today_date = datetime.strftime(datetime.today(),"%Y-%m-%d")
#
#     if form.validate_on_submit():
#
#         form_input= form_list(MCST_id=mcst_no,name= form.full_name.data,  contact_no = form.contact_no.data, date_registered = datetime.now(),
#                               unit = form.combine_unit_no() ,option= form.attending.data, form_id = form_id, email= form.email.data)
#
#         db.session.add(form_input)
#         db.session.commit()
#         flash('Thank You for the submission', 'success')
#         return redirect(url_for('mcst.form', mcst_no=mcst_no, form_id =form_id))
#
#
#
#     title = form_entry.description
#     return render_template(f'forms/sample_form_{form_id}.html' , mcst_info= mcst_info , form= form,
#                            estate_logo= estate_logo, today_date= today_date, title= title, user_info = user_info ,own_units=own_units,available_units =available_units )
