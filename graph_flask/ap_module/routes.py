import os
from flask import Blueprint, render_template,request, flash,redirect, url_for
from datetime import datetime

import requests

import graph_flask.config as config
ap_module = Blueprint('ap_module', __name__)





#
# @agm.route("/agmform/<int:mcst_no>/<int:form_id>/<int:user_id>", methods=['GET', 'POST'])
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
#     user_info = strata_roll.query.filter(strata_roll.agm_id == user_id).first()
#     print (user_info)
#     own_units = strata_roll.query.filter(strata_roll.subsidiary_proprietors == user_info.subsidiary_proprietors).filter(strata_roll.agm_id != user_id)
#     available_units = strata_roll.query.filter(strata_roll.MCST_id== user_info.MCST_id).filter(strata_roll.agm_id != user_id)
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
