import json
from dataclasses import dataclass
from pickle import TRUE
import pandas as pd
from sqlalchemy import desc, func, literal_column,select,or_,and_
from sqlalchemy.ext.hybrid import hybrid_property
from graph_flask import db, login_manager, ma, bcrypt
from flask_login import UserMixin, current_user
from flask_security import RoleMixin, SQLAlchemyUserDatastore
from datetime import datetime, date

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class user_project(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey('user.employee_id'), primary_key=True)
    project_id = db.Column(db.Integer(), db.ForeignKey('smart_project_listing.PRINTER_CODE'), primary_key=True)


class Job_title_role_relationship(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column('job_title_id', db.String(120), db.ForeignKey('job_title_role.jobTitle'))
    role_id = db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))
    job_title_name = db.relationship('job_title_role', secondary= Job_title_role_relationship.__table__,
                            backref=db.backref('role_list', lazy='dynamic'))
    def to_json(self):
        return{
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


class site_staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title_name = db.Column(db.String(120), db.ForeignKey('job_title_role.jobTitle'), nullable=False)
    mcst_no = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    site_email = db.Column(db.String(120))
    site_contact = db.Column(db.String(120))
    site_displayname = db.Column(db.String(120))
    attendance_register_list = db.relationship('attendance_register', backref='site_staff_info', lazy='dynamic')

    def to_json(self):
        return {
        'id':self.id,
        'jobTitle':self.job_title_name,
        'mcst_no':self.mcst_no,
        'email':self.site_email,
        'office_contact':self.site_contact,
        'displayname':self.site_displayname,
        }


class User(db.Model, UserMixin):
    # __tablename__ ="User"
    id = db.Column(db.Integer, primary_key=True)
    displayname = db.Column(db.String(100), unique=True, nullable=False)
    employee_id = db.Column(db.String(50),unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    jobTitle = db.Column(db.String(120), db.ForeignKey('job_title_role.jobTitle'), nullable=False)
    employeeName = db.Column(db.String(120), unique=False, nullable=False)
    azure_id = db.Column(db.String(120), unique=False, nullable=True)
    ManagerIncharge = db.Column(db.String(100),unique=False, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    termination_date = db.Column(db.Date, nullable=True)
    mobile_no = db.Column(db.String(120), unique=False, nullable=True)
    hq_direct_ext = db.Column(db.String(120), unique=False, nullable=True)
    project_list = db.relationship('smart_project_listing', secondary= user_project.__table__,
                            backref=db.backref('users_list', lazy='dynamic'))
    stationary_usage = db.relationship('stationary_usage', backref='user_info', lazy='dynamic')
    form_question_records= db.relationship('form_question_records', backref='user_info', lazy='dynamic')
    form_register= db.relationship('form_register', backref='user_info', lazy='dynamic')

    def get_all_child_users(self):
        user_list = [self]
        user_obj = self
        while user_obj.ManagerIncharge:
            user_obj = User.query.filter_by( employee_id=user_obj.ManagerIncharge).first()
            user_list.extend([user_obj])

        return user_list

    def manager_display_name(self):
        manager_obj = self.query.filter_by(employee_id = self.ManagerIncharge).first()
        return manager_obj.displayname if manager_obj else None

    def to_json(self):
        return {
            'id': self.id,
            'displayname': self.displayname,
            'employee_id': self.employee_id,
            'email': self.email,
            'jobTitle': self.jobTitle,
            'employeeName': self.employeeName,
            'department': self.jobTitleDetails.Department,
            'ManagerIncharge': self.manager_display_name(),
            'start_date': self.start_date,
            'termination_date' : self.termination_date,
            'mobile_contact':self.mobile_no,
            'office_contact':self.hq_direct_ext,
                }

    def __repr__(self):
        return f"User('{self.displayname}', '{self.email}', '{self.jobTitle}')"


class job_title_role(db.Model):
    
    jobTitle = db.Column(db.String(120), primary_key=True, unique=True, nullable=False)
    Department= db.Column(db.String(120), unique=False, nullable=False)
    jobTitle_shortform = db.Column(db.String(120), unique=True, nullable=False)
    jobTitleList = db.relationship('User', backref='jobTitleDetails', lazy='dynamic')
    siteStaffList = db.relationship('site_staff', backref='jobTitleDetails', lazy='dynamic')
    role_id = db.relationship('Role', secondary= Job_title_role_relationship.__table__,
                            backref=db.backref('job_title_list', lazy='dynamic'))


    def to_json(self):
        return {
            'jobTitle' : self.jobTitle,
            'Department' : self.Department,
        }


class bank_list(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    bank_full_name = db.Column(db.String(120))
    bank_short_name = db.Column(db.String(50))
    bank_code = db.Column(db.Integer)
    bank_contact_person = db.Column(db.String(50))
    bank_contact_no = db.Column(db.String(50))
    bank_contact_email = db.Column(db.String(120))
    bank_mailing_address = db.Column(db.String(120))
    bank_rate_list = db.relationship('bank_rates', backref='bank_info', lazy='dynamic')
    bank_accounts_list = db.relationship('bank_accounts', backref='bank_info', lazy='dynamic')


class bank_rates(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank_list.id') , nullable= False)
    account_type = db.Column(db.String(50))
    expense_type = db.Column(db.String(50))
    balancesheet_type = db.Column(db.String(50))
    signtype = db.Column(db.Boolean)
    
    
    def __repr__(self):
        return f"Account code('{self.account_code, self.account_description}')"


class bank_accounts(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    MCST_id =  db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    bank_id =  db.Column(db.Integer, db.ForeignKey('bank_list.id') , nullable= False)
    bank_account_no = db.Column(db.String(120))
    bank_branch_code = db.Column(db.Integer)
    account_type = db.Column(db.String(120))
    account_purpose = db.Column(db.String(120))
    bank_deposit_list = db.relationship('bank_fd_deposit', backref='bank_accounts_info', lazy='dynamic')
    bank_entries_list = db.relationship('bank_entry', backref='bank_accounts_info', lazy='dynamic')

    
    def net_amount(self, as_on_date = date.today()):
        return sum(bank_entry.bank_amt for bank_entry in self.bank_entries_list if bank_entry.trans_date <= as_on_date) + \
                 sum(fd_entry.initial_deposit_amt for fd_entry in self.bank_deposit_list if 
                 fd_entry.placement_date <= as_on_date and fd_entry.maturity_date >= as_on_date)

    def fd_entry_list(self , as_on_date = date.today()):
        return {
            'fd_list' :[fd_obj.to_json() for fd_obj in self.bank_deposit_list if fd_obj.placement_date <= as_on_date and fd_obj.maturity_date >= as_on_date]
        }
    def to_json(self): 
        return {
            'id' : self.id,
            'MCST_id' : self.MCST_id,
            'bank_shortform' : self.bank_info.bank_short_name,
            'bank_full_name' : self.bank_info.bank_full_name,
            'bank_account_no' : self.bank_account_no,
            'bank_branch_code' : self.bank_branch_code,
            'account_type' : self.account_type,
            'account_purpose' : self.account_purpose,
        }

    def to_json_details(self):

        acct_json = self.to_json()
        acct_json.update({"total_amount" : self.net_amount()})
        acct_json.update(self.fd_entry_list())

        return(acct_json)
        

class bank_entry(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    bank_acct_id =  db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    bank_amt =  db.Column(db.Float)
    trans_date = db.Column(db.Date)
    trans_desc = db.Column(db.String(120))
    trans_type = db.Column(db.String(120))


class bank_fd_deposit(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    bank_acct_id =  db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    interest_rate = db.Column(db.Float)
    initial_deposit_amt = db.Column(db.Float)
    deposit_no = db.Column(db.String(120))
    placement_date = db.Column(db.Date)
    maturity_date = db.Column(db.Date)

    def to_json(self):
        return {
        'id':self.id,
        'bank_acct_id':self.bank_accounts_info.bank_account_no,
        'interest_rate':self.interest_rate,
        'initial_deposit_amt':self.initial_deposit_amt,
        'deposit_no':self.deposit_no,
        'placement_date':self.placement_date,
        'maturity_date':self.maturity_date,
        }
@dataclass
class smart_project_listing(db.Model):
    MCST_no : str
    PRINTER_CODE : int
    PROPERTY_NAME : str
    START_DATE : datetime
    PREVIOUS_MA : str
    # TERMINATED_DATE : str
    NEW_MA : str
    UNITS : int
    BILLINGS_CYCLE : str
    SHAREPOINT_ID : str
    ROAD_NAME_ADDRESS : str
    OFFICIAL_ADDRESS : str
    MAILING_ADDRESS : str
    UEN_NO : str
    user_list: User
    # council_list : council_members
    # secList : SecRecords
    # printerLogList : printerLog

    MCST_no = db.Column(db.String(100), nullable=False)
    PRINTER_CODE = db.Column(db.Integer, nullable=False,primary_key=True)
    PROPERTY_NAME =  db.Column(db.String(100), nullable=False)
    START_DATE =  db.Column(db.Date, nullable=True)
    PREVIOUS_MA =  db.Column(db.String(100), nullable=True)
    TERMINATED_DATE= db.Column(db.Date, nullable=True)
    NEW_MA = db.Column(db.String(100), nullable=True)
    UNITS =  db.Column(db.Integer, nullable=False)
    BILLINGS_CYCLE = db.Column(db.String(100), nullable=True)
    SHAREPOINT_ID = db.Column(db.String(100), nullable=True)
    ROAD_NAME_ADDRESS = db.Column(db.String(100), nullable=True)
    OFFICIAL_ADDRESS = db.Column(db.String(100), nullable=True)
    MAILING_ADDRESS = db.Column(db.String(100), nullable=True)
    UEN_NO = db.Column(db.String(100), nullable=True)
    user_list = db.relationship(User, secondary=user_project.__table__,
                                   backref=db.backref('projects_list', lazy='dynamic'))
    council_list = db.relationship('council_members', backref= 'projectDetails', lazy = 'dynamic')
    secList = db.relationship('SecRecords', backref='projectDetails', lazy='dynamic')
    printerLogList = db.relationship('printerLog', backref='projectDetails', lazy='dynamic')
    form_register = db.relationship('form_register', backref='projectDetails', lazy='dynamic')
    stationary_adjusted_price_list = db.relationship('stationary_adjusted_price', backref='projectDetails', lazy='dynamic')
    paynow_list = db.relationship('paynow_data', uselist = False, backref='projectDetails')
    site_staff_list = db.relationship('site_staff', backref='projectDetails', lazy='dynamic')
    bank_account_list = db.relationship('bank_accounts', backref='projectDetails', lazy='dynamic')
    vendor_invoice_list = db.relationship('vendors_invoice', backref='projectDetails', lazy='dynamic')
     

    # financialYearList = db.relationship('financialYear', backref='projectDetails', lazy='dynamic')
    # agmList = db.relationship('agmList', backref='projectDetails', lazy='dynamic')
    # agmBudgetList = db.relationship('budget', backref='projectDetails', lazy='dynamic')
    @hybrid_property
    def accounts_in_charge(self):
        return  [user.displayname for user in self.user_list if user.jobTitleDetails.Department == "Finance"]
    
    @hybrid_property
    def operations_in_charge(self):
        return  [user.displayname for user in self.user_list if "Operations" in user.jobTitleDetails.Department]    
    
    @hybrid_property
    def site_in_charge(self):
        return  [user.displayname for user in self.user_list if user.jobTitleDetails.Department == "Site"]    
    

    def get_all_child_users_project(self, user_obj,incharge, user_list=[]):
        if user_obj:
            user_obj.incharge = incharge
            if not user_obj in user_list :  user_list.extend([user_obj])
            incharge = False
            manager_user = User.query.filter_by(employee_id=user_obj.ManagerIncharge).first()
            if manager_user:
                self.get_all_child_users_project(user_obj= manager_user, incharge=incharge, user_list=user_list)
            else:
                incharge = True
        return user_list

    def to_json(self):
        return {
                'PRINTER_CODE': self.PRINTER_CODE,
                'PROPERTY_NAME': self.PROPERTY_NAME,
                'START_DATE': self.START_DATE,
                'PREVIOUS_MA': self.PREVIOUS_MA,
                'TERMINATED_DATE': self.TERMINATED_DATE,
                'NEW_MA': self.NEW_MA,
                'UNITS': self.UNITS,
                'BILLINGS_CYCLE': self.BILLINGS_CYCLE,                
                'ROAD_NAME_ADDRESS': self.ROAD_NAME_ADDRESS,
                'OFFICIAL_ADDRESS': self.OFFICIAL_ADDRESS,
                'MAILING_ADDRESS': self.MAILING_ADDRESS,
                'UEN_NO': self.UEN_NO,
        }
    
    def user_count_json(self):
        return {
                'FINANCE_IN_CHARGE': self.accounts_in_charge,
                'OPERATION_IN_CHARGE': self.operations_in_charge,
                'SITE_IN_CHARGE': self.site_in_charge
        }
    
    def user_list_json(self):
        user_list = []
        for user in self.user_list : user_list = self.get_all_child_users_project(user_obj=user, user_list=user_list, incharge=True)
        return {
                'user_list': [{**user_obj.to_json(),**{'incharge': user_obj.incharge}}
                           for user_obj in user_list]
        }

    def site_staff_list_json(self):
        return {
            'site_user_list':  [site_staff_obj.to_json() for site_staff_obj in self.site_staff_list]
        }

    def bank_account_json(self):
        return {
            'bank_accounts':  [bank_account_obj.to_json_details() for bank_account_obj in self.bank_account_list]
        }

    def outstanding_invoices(self, as_on_period=date.today()):
        payment_invoice =  db.session.query(vendors_payment.invoice_id, db.func.sum(vendors_payment.payment_amount).label("payment_amount")).group_by(
                            vendors_payment.invoice_id).filter(vendors_payment.payment_date <= as_on_period).cte("payment")
        vendor_invoices = db.session.query(payment_invoice.c.payment_amount ,vendors_invoice, vendors_details.vendor_name.label('name')).\
                            select_from(vendors_invoice).\
                            outerjoin(payment_invoice,payment_invoice.c.invoice_id== vendors_invoice.id).\
                            join(vendors_details,vendors_invoice.vendor_name==vendors_details.id).\
                            filter(and_(vendors_invoice.MCST_id==self.PRINTER_CODE,
                            or_(func.round(payment_invoice.c.payment_amount+vendors_invoice.invoice_amt,2)!=0,
                            payment_invoice.c.payment_amount==None),
                            vendors_invoice.invoice_date <= as_on_period)).\
                            cte('vendor_invoices')
        return db.session.query(vendor_invoices).all()
    

    def outstanding_vendor_amount(self, as_on_period=date.today()):
        return [(outstanding_invoice.name, outstanding_invoice.invoice_date, outstanding_invoice.invoice_ref ,outstanding_invoice.payment_amount if outstanding_invoice.payment_amount else 0  + outstanding_invoice.invoice_amt)
          for outstanding_invoice in self.outstanding_invoices(as_on_period=as_on_period)]

    def total_outstanding_vendor_amount(self, as_on_period=date.today()):

        return round(sum([(outstanding_invoice.payment_amount if outstanding_invoice.payment_amount else 0   + outstanding_invoice.invoice_amt)
          for outstanding_invoice in self.outstanding_invoices(as_on_period=as_on_period)]),2)


    def to_info_json(self):
        json_dict = self.to_json()
        json_dict.update(self.user_list_json())
        json_dict.update(self.site_staff_list_json())
        json_dict.update(self.bank_account_json())
        return json_dict

    def __repr__(self):
        return f"Project_listing('{self.MCST_no}', '{self.PROPERTY_NAME}')"


class paynow_data(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    MCST_id =  db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    paynow_uen = db.Column(db.String(120))
    activation_date = db.Column(db.Date)
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=True)


class approvalMatrix(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    MCST_id = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    lowerLimit = db.Column(db.String(120), nullable = False)
    upperLimit = db.Column(db.String(120), nullable=False)
    requireNumber = db.Column(db.Integer, nullable=False)
    officeBearerRequired = db.Column(db.Boolean, nullable=False)


class council_members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    MCST_id = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    name = db.Column(db.String(120), nullable = False)
    email =  db.Column(db.String(120))
    contact_no = db.Column(db.String(120))
    position = db.Column(db.String(120))
    dateOfAppt = db.Column(db.String(120))
    dateOfCease = db.Column(db.String(120))


class lawyerFirm(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    lawFirmName = db.Column(db.String(120))
    lawFirmAddress = db.Column(db.String(120))
    lawFirmContactPerson = db.Column(db.String(120))
    lawFirmContactNo = db.Column(db.String(120))
    lawFirmEmail = db.Column(db.String(120))
    lawFirmFax = db.Column(db.String(120))
    secList = db.relationship('SecRecords', backref='lawyerDetails', lazy='dynamic')

    def __repr__(self):
        return f"Lawyer Firm('{self.lawFirmName}')"


class SecRecords(db.Model):
    id = db.Column(db.Integer,nullable= False, primary_key=True)
    MCST_id = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    laywerId = db.Column(db.Integer, db.ForeignKey('lawyer_firm.id'), nullable=False)
    applicantControlNo = db.Column(db.String(120), nullable = True)
    unitAccountNo = db.Column(db.String(120) , nullable= False)
    laywerRef = db.Column(db.String(120))
    applyDate = db.Column(db.String(120))
    completionDate = db.Column(db.String(120))
    status = db.Column(db.String(120))


class printerLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    MCST_id = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    printerModel = db.Column(db.String(120))
    printerJobNo = db.Column(db.String(120))
    printDateTime = db.Column(db.String(120))
    printType = db.Column(db.String(120))
    printFileName = db.Column(db.String(120))
    printUserName = db.Column(db.String(120))
    printSheetPages = db.Column(db.Integer)
    printCopies = db.Column(db.Integer)
    printStatus = db.Column(db.String(120))


class meeting_register(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    meeting_topic = db.Column(db.String(120))
    meeting_date = db.Column(db.DateTime)
    attendance_list = db.relationship('attendance_register', backref='meeting_info', lazy='dynamic')


class attendance_register(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting_register.id'),nullable=False)
    hq_user_email = db.Column(db.String(120), db.ForeignKey('user.email'))
    site_staff_id = db.Column(db.Integer, db.ForeignKey('site_staff.id'))
    attending = db.Column(db.Boolean)
    pre_meeting_question = db.Column(db.String)
    last_modified_date = db.Column(db.DateTime)
    locked = db.Column(db.Boolean)
    additional_participants = db.relationship('add_attendance_participant_register', backref='register_info', lazy='dynamic')

    def to_json(self):
        return {
            'id' : self.id,
            'meeting_id':self.meeting_id,
            'meeting_topic': self.meeting_info.meeting_topic,
            'meeting_date': self.meeting_info.meeting_date,
            'hq_user_name':self.hq_user_email if self.hq_user_email else None,
            'site_staff_email': self.site_staff_info.site_email if self.site_staff_id else None,
            'attending':self.attending,
            'pre_meeting_question':self.pre_meeting_question,
            'last_modified_date': self.last_modified_date,
            'locked': self.locked,
            'additional_participants': [add_participants.to_json() for add_participants in self.additional_participants],
        }
     

class add_attendance_participant_register(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    attendance_register_id = db.Column(db.Integer, db.ForeignKey('attendance_register.id'),nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    position = db.Column(db.String(120))
    

    def to_json(self):
        return {
        'id':self.id,
        # 'attendance_register_id':self.attendance_register_id,
        'display_name':self.display_name,
        'email':self.email,
        'position':self.position,
        }


class form_register(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    MCST_id =  db.Column(db.Integer,db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    form_template = db.Column(db.Integer, db.ForeignKey('form_template.id'),nullable=True)
    form_records = db.relationship('form_question_records', backref = 'form_register_details', lazy='dynamic')
    last_modified_by = db.Column(db.String(120), db.ForeignKey('user.email'),nullable=False)
    last_modified_date = db.Column(db.DateTime)
    date_creation = db.Column(db.Date)
    form_open = db.Column(db.Boolean)

    def to_json(self):
        return {
            'id' : self.id,
            'MCST_id' : self.MCST_id,
            'mcst_name' : self.projectDetails.PROPERTY_NAME,
            'form_template' : self.form_info.form_description,
            'last_modified_by' : self.user_info.displayname,
            'last_modified_date' : self.last_modified_date,
            'date_creation' : self.date_creation,
            'form_open' : self.form_open,
        }
   

class form_template(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    form_name = db.Column(db.String(120))
    form_description = db.Column(db.String(120))
    form_sub_category = db.relationship('form_sub_category', backref = 'form_info', lazy='dynamic')
    form_register_list = db.relationship('form_register', backref = 'form_info', lazy='dynamic')

    def to_json(self):
        return {
            'id':self.id,
            'form_name':self.form_name,
            'form_description':self.form_description,           
        }

    def __repr__(self) -> str:
        return f'form_template {self.form_name}'


class form_sub_category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sub_category_name = db.Column(db.String(120))
    form_template = db.Column(db.Integer, db.ForeignKey('form_template.id') , nullable= False)
    form_question = db.relationship('form_question', backref = 'form_sub_category_details', lazy='dynamic')

    def __repr__(self) :
        return f'form_sub_category {self.sub_category_name}'


class form_question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_string = db.Column(db.String(120))
    question_type = db.Column(db.String(120))
    question_option = db.Column(db.String(120))
    sub_category_id = db.Column(db.Integer, db.ForeignKey('form_sub_category.id'), nullable=False)
    form_question_records = db.relationship('form_question_records', backref = 'form_question_details', lazy='dynamic')

    def to_json(self):
        return { 
            'id':self.id,
            'question_string':self.question_string,
            'question_type':self.question_type,
            'question_option':self.question_option,
            'sub_category':self.form_sub_category_details.sub_category_name,
        }

    def to_json_with_records(self, form_register_id):
        form_question_record =  self.form_question_records.filter_by(form_register_id=form_register_id).first()       
        return { 
            'id':self.id,
            'question_string':self.question_string,
            'question_type':self.question_type,
            'question_option':self.question_option,
            'sub_category':self.form_sub_category_details.sub_category_name,
            'question_records': form_question_record.question_record if form_question_record else None
        }


class form_question_records(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('form_question.id'), nullable=False)
    form_register_id = db.Column(db.Integer, db.ForeignKey('form_register.id'), nullable=False)
    question_record = db.Column(db.String(120))
    date_of_record = db.Column(db.DateTime)
    modified_by = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=True)   
    records_details =  db.relationship('form_question_records_details', backref = 'form_record_details', lazy='dynamic')

    def to_json(self):
        return {
            'id' : self.id,
            'question_id' : self.question_id,
            'form_register_id' : self.form_register_id,
            'question_record' : self.question_record,
            'date_of_record' : self.date_of_record,
            'modified_by' : self.modified_by,
        }  


class form_question_records_details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_question_records_id = db.Column(db.Integer, db.ForeignKey('form_question_records.id'), nullable=False)
    details_list = db.Column(db.String(120))
    date_of_record = db.Column(db.DateTime)
    modified_by = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=True)   
    image_attached_file = db.Column(db.String(120))

    def save_path(self):
        question_id = self.form_record_details.question_id
        form_template = self.form_record_details.form_question_details.form_sub_category_details.form_info
        form_register = self.form_record_details.form_register_id
        return f'{form_template.id:03d} - {form_template.form_name}/{form_register:03d}/{question_id:03d}'

    def to_json(self):
        return {
            'id' : self.id,
            'form_question_records_id' : self.form_question_records_id,
            'details_list' : self.details_list,
            'date_of_record' : self.date_of_record,
            'modified_by' : self.modified_by,
            'image_attached_file' : self.image_attached_file,
        }  


class strata_roll_unit(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    MCST_id =  db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    unit_account =  db.Column(db.String(120))
    blk = db.Column(db.String(120))
    unit = db.Column(db.String(120))
    subsidiary_proprietors  = db.Column(db.String(120), nullable=False)
    share = db.Column(db.String(120))
    official_address = db.Column(db.String(120))
    mailing_address=  db.Column(db.String(120))
    strata_roll_users = db.relationship('strata_roll_user', backref = 'strata_roll_info', lazy='dynamic')
    
    def encrypt_pdpa(self):
        self.subsidiary_proprietors = bcrypt.generate_password_hash(self.subsidiary_proprietors).decode('utf-8')
        self.mailing_address = bcrypt.generate_password_hash(self.mailing_address).decode('utf-8')
        if self.contact_person :
           self.contact_person = bcrypt.generate_password_hash(self.contact_person).decode('utf-8')
        if self.contact_no:
            self.contact_no = bcrypt.generate_password_hash(self.contact_no).decode('utf-8')
        if self.email:
            self.email = bcrypt.generate_password_hash(self.email).decode('utf-8')
    
    def get_unit_no(self):
        return {
            'unit_account' : self.unit_account,
            'subsidiary_proprietors' : self.subsidiary_proprietors,
        }

    def __repr__(self):
        return f'strall_roll({self.MCST_id},{self.unit_account})'


class strata_roll_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(120))
    contact_person = db.Column(db.String(120))
    contact_no = db.Column(db.String(120))
    email =  db.Column(db.String(120))
    strata_roll_unit_id = db.Column(db.Integer, db.ForeignKey('strata_roll_unit.id') , nullable= False)


class vendors_details(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    vendor_name =  db.Column(db.String(120))
    vendor_uen = db.Column(db.String(120))
    vendor_address= db.Column(db.String(120))
    vendor_email  = db.Column(db.String(120))
    vendor_phone= db.Column(db.String(120))
    vendor_bank_account= db.Column(db.String(120))
    vendor_paynow=  db.Column(db.String(120))
    gst_registered = db.Column(db.Boolean)
    vendor_name_match = db.relationship('vendors_name_match', backref='vendor_details', lazy='dynamic')
    
    def __repr__(self):
        return f'vendor({self.id},{self.vendor_name})'

    def outstanding_invoices(self, as_on_period= date.today() , mcst_no= None):
        if mcst_no :
            return [invoice for invoice in self.vendor_invoice_list.all() if invoice.outstanding_amt(as_on_period) > 0 and invoice.MCST_id == mcst_no]
        else:
            
            return [invoice for invoice in db.session.query(vendors_details,vendors_invoice)]

    def search_payment_log(self, payment_ref = None, payment_amount=None, mcst_no =None):
        
        payment_ref_group =  db.session.query(vendors_details.vendor_name, 
                            vendors_invoice.MCST_id, vendors_payment.payment_reference,
                            vendors_payment.payment_amount.label("payment_amount"),
                            vendors_invoice.invoice_ref).\
                            select_from(vendors_payment).\
                            join(vendors_invoice).\
                            join(vendors_details).\
                            filter(vendors_details.id==self.id).\
                            cte('vendor_payment_ref')
        group_ref_group =   db.session.query(db.func.sum(payment_ref_group.c.payment_amount).label('payment_amount'),
                            db.func.string_agg(payment_ref_group.c.invoice_ref, literal_column("','")).label('invoice_ref_list'),
                            payment_ref_group.c.payment_reference,
                            payment_ref_group.c.vendor_name,
                            payment_ref_group.c.MCST_id).\
                            group_by(payment_ref_group.c.payment_reference,payment_ref_group.c.vendor_name,
                            payment_ref_group.c.MCST_id).\
                            cte("group_ref_group")
                            
        if payment_ref : group_ref_group  =db.session.query(group_ref_group).filter(group_ref_group.c.payment_reference==payment_ref).cte("vendor_payment_ref_filter_ref")
        if payment_amount : group_ref_group  =db.session.query(group_ref_group).filter(group_ref_group.c.payment_amount==payment_amount).cte("vendor_payment_ref_filter_amt")
        if mcst_no : group_ref_group  =db.session.query(group_ref_group).filter(group_ref_group.c.MCST_id== mcst_no).cte("vendor_payment_ref_filter_mcst")

        return db.session.query(group_ref_group).all()
        
class vendors_name_match(db.Model):        
    id = db.Column(db.Integer, primary_key=True)
    vendor_ap_name =  db.Column(db.String(120))
    vendor_id = db.Column(db.Integer,db.ForeignKey('vendors_details.id'), nullable = True)
    vendor_invoice_list = db.relationship('vendors_invoice', backref='vendor_name_match', lazy='dynamic')
    vendor_purchase_list = db.relationship('vendors_purchase', backref='vendor_name_match', lazy='dynamic')

class vendors_purchase(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    MCST_id = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    vendor_name = db.Column(db.Integer,db.ForeignKey('vendors_name_match.id'), nullable = False)
    approved_date = db.Column(db.Date)
    clearance_date = db.Column(db.Date)
    contract_ref= db.Column(db.String(120))
    ad_hoc_ref = db.Column(db.String(120))
    invoice_list = db.relationship('vendors_invoice', backref = 'purchase_info', lazy = 'dynamic')

class vendors_invoice(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer,db.ForeignKey('vendors_name_match.id'), nullable = False)
    purchase_id = db.Column(db.Integer,db.ForeignKey('vendors_purchase.id'))
    MCST_id = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    invoice_ref = db.Column(db.String(120))
    invoice_date = db.Column(db.Date)
    invoice_amt = db.Column(db.Float)
    invoice_gst = db.Column(db.String(120))
    service_ref = db.Column(db.String(120))
    invoice_gl_list = db.relationship('vendors_gl', backref = 'invoice_info', lazy = 'dynamic')
    payment_list = db.relationship('vendors_payment', backref = 'invoice_info', lazy = 'dynamic')
    payment_description = db.Column(db.String, nullable=False)
    

    def __repr__(self):
        return f'vendor_invoice({self.MCST_id},{self.vendor_name},{self.invoice_ref})'

    
    def outstanding_amt(self, as_on_period=date.today()):
        return self.invoice_amt + sum(payment_obj.payment_amount for payment_obj in self.payment_list if payment_obj.payment_date <= as_on_period)
            
    # @outstanding_amt.expression
    # def outstanding_amt(cls):
    #     return db.session.query(vendors_payment.invoice_id==cls.id).all() + cls.invoice_amt
    #     # func.sum(cls.invoice_amt,

class vendors_payment(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer,db.ForeignKey('vendors_invoice.id'))
    payment_reference=  db.Column(db.String(120))
    payment_type = db.Column(db.String(120))
    payment_date = db.Column(db.Date)
    payment_amount = db.Column (db.Float)

    


class vendors_gl(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    vendor_invoice_id = db.Column(db.Integer,db.ForeignKey('vendors_invoice.id'))
    gl_account_code = db.Column(db.String(120))
    gl_entry_description = db.Column(db.String(120))
    gl_period_start = db.Column(db.String(120))
    gl_period_end = db.Column(db.String(120))
    gl_amount = db.Column(db.String(120))

    def __repr__(self):
        return f'vendor_gl_list({self.MCST_id},{self.vendor_name},{self.invoice_ref})'


class gl_listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Mcst_no = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)
    account_code =  db.Column(db.Integer,db.ForeignKey('account_code_listing.account_code') , nullable=False)
    account_dept = db.Column(db.String(50), nullable=False)
    item_date = db.Column(db.String(50), nullable=False)
    debit_credit_amt = db.Column(db.Text, nullable=False)
    reference = db.Column(db.String(50))
    debtor_creditor = db.Column(db.String(50))
    description = db.Column(db.String(50))
    status = db.Column(db.String(50))
    # audit_description = db.Column(db.String(50), db.ForeignKey('audit_income_expenditure.audit_description'))

    def __repr__(self):
        return f"GL listing('{self.Mcst_no, self.account_code, self.account_description, self.debit_credit_amt})'"


class account_code_listing(db.Model):
    account_code = db.Column(db.Integer, primary_key = True)
    account_description = db.Column(db.String(50), nullable=False)
    account_type = db.Column(db.String(50))
    expense_type = db.Column(db.String(50))
    balancesheet_type = db.Column(db.String(50))
    signtype = db.Column(db.Boolean)
    short_name = db.Column(db.String(50))

    def __repr__(self):
        return f"Account code('{self.account_code, self.account_description}')"


class stationary_type(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    item_type = db.Column(db.String(50), nullable=False)
    item_group = db.Column(db.String(50), nullable=False)
    item_price = db.Column(db.Float)
    stationary_usage = db.relationship('stationary_usage', backref='stationary_details', lazy='dynamic')
    stationary_adjusted_price = db.relationship('stationary_adjusted_price', backref='stationary_details', lazy='dynamic')
    stationary_topup_list = db.relationship('stationary_topup', backref='stationary_details', lazy='dynamic')


    def revised_price(self, mcst):
        revised_item = self.stationary_adjusted_price.filter_by(item_mcst = mcst).first()
        return revised_item.item_adjusted_price if revised_item else self.item_price

    def to_json(self):
        return {
                'id': self.id,
                'item_type': self.item_type,
                'item_group': self.item_group,}

    def total_topup(self):
        total_topup_amt = db.session.query(db.func.sum(stationary_topup.topup_quantity)
                        ).filter(stationary_topup.usage_type == self.id).all()
        return total_topup_amt[0][0] 
    
    def total_usage(self):
        total_usage_amt = db.session.query(db.func.sum(stationary_usage.usage_quantity)
                        ).filter(stationary_usage.usage_type == self.id).all()
        return total_usage_amt[0][0] 
    
    def remain_stock(self):
        total_usage_amt = self.total_usage()
        total_topup = self.total_topup()

        if total_usage_amt and total_topup : 
            return total_topup - total_usage_amt            
        
        return "No records" 

    def to_stock_json(self):
        return {
            'item_id' : self.id,
            'item_stock' : self.remain_stock()
        }

    def last_topup(self):
        last_topup_entry = db.session.query(stationary_topup).filter(
            stationary_topup.usage_type == self.id).order_by(desc(stationary_topup.topup_date)).first()
        
        return last_topup_entry.topup_quantity if last_topup_entry else 0

    def __repr__(self):
        return f"Stationary ('{self.item_group, self.item_type}')"


class stationary_adjusted_price(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    item_type = db.Column(db.Integer, db.ForeignKey('stationary_type.id'), nullable=False)   
    item_mcst = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)   
    item_adjusted_price = db.Column(db.Float)
    
    def __repr__(self):
        return f'Adjusted Stationary Price {self.item_mcst} {self.stationary_details.item_type} {self.item_adjusted_price}'


class stationary_usage(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    usage_mcst = db.Column(db.Integer, db.ForeignKey('smart_project_listing.PRINTER_CODE'), nullable=False)   
    usage_type = db.Column(db.Integer, db.ForeignKey('stationary_type.id'), nullable=False)   
    usage_date = db.Column(db.Date, nullable=True)
    usage_purpose = db.Column(db.String(100), nullable=True)
    usage_quantity = db.Column(db.Float, nullable=False)
    usage_user = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=True)   

    def to_json(self):
        displayname = self.user_info.displayname if self.usage_user else ""
        return {
                'id': self.id,
                'usage_mcst': self.usage_mcst,
                'usage_type': self.stationary_details.item_type,
                'usage_group': self.stationary_details.item_group,
                'usage_date': self.usage_date,
                'usage_purpose': self.usage_purpose,
                'usage_quantity': self.usage_quantity,
                'usage_user': displayname}


    def __repr__(self):
        return f"Stationary usage ('{self.usage_type, self.usage_quantity}')"


class stationary_topup(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    usage_type = db.Column(db.Integer, db.ForeignKey('stationary_type.id'), nullable=False)   
    topup_date = db.Column(db.Date, nullable=True)
    topup_quantity = db.Column(db.Float, nullable=False)

    def to_json(self):
        
        return {
                'id': self.id,
                'usage_type': self.stationary_details.item_type,
                'topup_date': self.topup_date,
                'topup_quantity': self.topup_quantity,
        }

    def __repr__(self):
        return f"Stationary usage ('{self.usage_type, self.topup_quantity}')"


class function_list(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    function_name = db.Column(db.String(120), nullable=True)
    function_desc = db.Column(db.String(120), nullable=True)
    function_field_required = db.Column(db.String(120), nullable=True)

    def to_json(self):
        return {
            'id':self.id,
            'function_name':self.function_name,
            'function_desc':self.function_desc,
            'function_field_required':self.function_field_required,    
        }


class portfolio_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    displayname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    last_login = db.Column(db.DateTime)
    ratings_records= db.relationship('ratings_record', backref='porfolio_user_info', lazy='dynamic')
    testimonial_records= db.relationship('portfolio_testimonial', backref='porfolio_user_info', lazy='dynamic')

    def rating_records_json(self):

        rating_records = db.session.query(ratings_record.id, ratings_record.rating_score, ratings_record.portfolio_user_id, portfolio_project.project_name, 
                        ratings_record.rating_type_id, rating_type.rating_name).\
                        select_from(ratings_record).\
                        join(portfolio_user,portfolio_user.id == ratings_record.portfolio_user_id).\
                        join(portfolio_project,portfolio_project.id == ratings_record.portfolio_project_id).\
                        join(rating_type,rating_type.id == ratings_record.rating_type_id).\
                        filter(portfolio_user.id == self.id).all()
        
        return ([{key:getattr(ratings_record_query,key) for key in ratings_record_query.keys()} for ratings_record_query in rating_records])
    
    def to_json(self):
        
        return ({
            'id':self.id,
            'displayname':self.displayname,
            'email':self.email,
            'last_login':self.last_login,
            'rating_records': self.rating_records_json()
        })
                

    

class portfolio_project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(120), nullable=False)
    video_link = db.Column(db.String(120))
    project_tag= db.Column(db.String(120))
    ratings_records= db.relationship('ratings_record', backref='porfolio_project_info', lazy='dynamic')

    def rating_list_to_json(self):

        rating_list = db.session.query(func.avg(ratings_record.rating_score).label('average_score'), 
                    ratings_record.rating_type_id, rating_type.rating_name, portfolio_project.project_name).\
                    select_from(ratings_record).\
                    join(rating_type, ratings_record.rating_type_id== rating_type.id).\
                    join(portfolio_project, ratings_record.portfolio_project_id == portfolio_project.id).\
                    group_by(ratings_record.rating_type_id, rating_type.rating_name, portfolio_project.project_name).\
                    filter(portfolio_project.id ==  self.id).all()
        
        return ([{key:getattr(ratings_record_query,key) for key in ratings_record_query.keys()} for ratings_record_query in rating_list])

    def to_json(self):
        return ({
            'id':self.id,
            'project_name':self.project_name,
            'video_link':self.video_link,
            'project_tag':self.project_tag,
            'rating_mean_score' : self.rating_list_to_json()
        })

class portfolio_testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    testimonial_text = db.Column(db.String(120))
    testimonial_rating =  db.Column(db.Float)
    testimonial_date = db.Column(db.DateTime)
    portfolio_user_id = db.Column(db.Integer, db.ForeignKey('portfolio_user.id'), nullable=False) 

    def to_json(self):
        return ({
        'id': self.id,
        'testimonial_text': self.testimonial_text,
        'testimonial_rating': self.testimonial_rating,
        'testimonial_date': self.testimonial_date.strftime("%d/%m/%y"),
        'testimonial_user': self.porfolio_user_info.displayname
        })


class rating_type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating_name = db.Column(db.String(120), nullable=False)
    max_rating = db.Column(db.Integer)
    ratings_records= db.relationship('ratings_record', backref='rating_type_info', lazy='dynamic')


class ratings_record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating_score = db.Column(db.Integer)
    portfolio_user_id = db.Column(db.Integer, db.ForeignKey('portfolio_user.id'), nullable=False)   
    portfolio_project_id = db.Column(db.Integer, db.ForeignKey('portfolio_project.id'), nullable=False)   
    rating_type_id = db.Column(db.Integer, db.ForeignKey('rating_type.id'), nullable=False)   
