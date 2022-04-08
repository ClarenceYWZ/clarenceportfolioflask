from datetime import datetime, time, timedelta, date
import re
from numpy.core.defchararray import index
import requests
import os
import json
import io
import base64
from fpdf import FPDF
import pandas as pd
import numpy as np
import concurrent.futures
import fitz
from PIL import Image
from cryptography.fernet import Fernet
from graph_flask.models import db, stationary_adjusted_price, stationary_usage, stationary_type, smart_project_listing
from graph_flask.microsoft.utils import folder_graph_api,mcst_template_header
from graph_flask.ar_module.utils import qr_code_generate_smart


headers = {
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

class printing_class():
    SEC47_ID = 18
    
    def __init__(self,report_date):
        # super(printing_class,self).__init__()
        self.machine = {
            'CANON C5540' :{'id_col': 'Dept. ID', 'print_col_list' :  ['Black & White Total', 'Color Total']},
            'CANON C3320' :{'id_col': 'Dept. ID', 'print_col_list' : ['Black & White Total', 'Color Total']},
            'RICOH C3503' :{'id_col': 'User', 'print_col_list' : ['B & W(Total Prints)', 'Color (Total Prints)']},
            'TOSHIBA 5015AC' :{'id_col': 'Department Code', 'print_col_list' : ['Printer Black small', 'Printer Full Color small','Department Code']},
        }
        self.report_date = report_date
        self.file_path = f'CLOSED STATIONERY BILLING\{self.report_date.strftime("%Y")}' \
                    f'\{self.report_date.strftime("%m")} - {self.report_date.strftime("%b").upper()}' \
                    f'-{self.report_date.strftime("%y")}'    

    def folder_graph(self) :
        return folder_graph_api()

    def check_import_record(self,  report_type):

        return bool(len(stationary_usage.query.filter(stationary_usage.usage_date <= self.report_date , 
        stationary_usage.usage_date >=self.report_date.replace(day=1), 
        stationary_usage.usage_purpose.contains(report_type)).all()))
            
    def import_copier_report(self, photocopy_report_pd, machine_model = "CANON C5540"):
        id_col, print_col_list = self.machine.get(machine_model)['id_col'], self.machine.get(machine_model)['print_col_list']
        
        # check last and drop last row
        if photocopy_report_pd.tail(1)[id_col].isna().values : photocopy_report_pd.drop(photocopy_report_pd.tail(1).index, inplace=True)
        # remove bracket from id col
        if photocopy_report_pd[id_col].dtype in ["str","object"]: photocopy_report_pd[id_col] = photocopy_report_pd[id_col].str.extract('(\d+)')
        photocopy_report_pd.astype({id_col: 'int32'})
        usage_type_list = [usage_type for usage_type in stationary_type.query.filter(stationary_type.item_type.in_(['Printing B/W A4 Paper','Printing Color / Inv Billing']))]
        for id, bw_printing, color_printing  in zip(photocopy_report_pd[id_col] ,photocopy_report_pd[print_col_list[0]],photocopy_report_pd[print_col_list[1]]):
            quantity_list = [bw_printing, color_printing]
            if not smart_project_listing.query.get(id) : 
                print_code = id
                id = 8888
            if smart_project_listing.query.get(id).TERMINATED_DATE < date(self.report_date.year,self.report_date.month ,1) : 
                print_code = id
                id = 8888
            for usage_type, usage_quantity in zip(usage_type_list,quantity_list):
                if usage_quantity:
                    new_stationary_record = stationary_usage(
                        usage_mcst= id,
                        usage_type=usage_type.id,
                        usage_date= self.report_date,
                        usage_purpose= f'Monthly Printing Records {machine_model} {f"({print_code})" if id == 8888 else ""}',
                        usage_quantity = usage_quantity)
                    db.session.add(new_stationary_record)

        db.session.commit()

    def import_franking_report(self, franking_report_pd):
        franking_report_pd = franking_report_pd.groupby(['MailingDate','Product','Account1Name', 'Baserate'])['Country', 'TotalPostage'].agg({
            'Country': lambda x : x.count(),
            'TotalPostage' : 'sum'
        })
        franking_report_pd =  franking_report_pd.reset_index()
        franking_report_pd['Account1Name']  =franking_report_pd['Account1Name'].str.extract(r'^(\d+)\s+')
        usage_type_list = [stationary_type.query.filter(stationary_type.item_type=='Franking').first(),
                        stationary_type.query.filter(stationary_type.item_type=='DL').first()]
        
        for _, item in franking_report_pd.iterrows():
    
            id = 8888 if not smart_project_listing.query.get(item['Account1Name']) else item['Account1Name']
            for usage_type, usage_quantity in zip(usage_type_list,[item['TotalPostage'], item['Country']]):
                new_stationary_record = stationary_usage(
                        usage_mcst= id,
                        usage_type=usage_type.id,
                        usage_date= datetime.strptime(item['MailingDate'],"%d/%m/%Y"),
                        usage_purpose= f'Franking Records {item["Country"]} X ${item["Baserate"]:.2f} {item["Product"]}',
                        usage_quantity =  round(usage_quantity,2))
                db.session.add(new_stationary_record)
        db.session.commit()
        return franking_report_pd
    def import_crimsion_report(self, crimsion_report_pd):
        crimsion_report_pd['REPLIED / BILLING DATE'] = pd.to_datetime(crimsion_report_pd['REPLIED / BILLING DATE'])
        filter_pd = crimsion_report_pd[(crimsion_report_pd['REPLIED / BILLING DATE'].dt.month == self.report_date.month) &
        (crimsion_report_pd['REPLIED / BILLING DATE'].dt.year == self.report_date.year)]
        filter_pd = filter_pd.fillna('')
        filter_pd.astype({'MCST / SUB-MCST NO' : 'int32', 'UNIT NO': 'string'})
        for _, crimsion_entry in filter_pd.iterrows():
            new_stationary_record = stationary_usage(usage_mcst= crimsion_entry['MCST / SUB-MCST NO'], 
            usage_type=self.SEC47_ID,
            usage_date=crimsion_entry['REPLIED / BILLING DATE'],
            usage_purpose= f"Blk {crimsion_entry['BLOCK NO']} #{crimsion_entry['UNIT NO'].replace(' ','')} \n"
                           f"Crimsion Ref {crimsion_entry['LF CONTROL NO']}",
            usage_quantity = 1)
            db.session.add(new_stationary_record) 

        db.session.commit()
    
    def import_toppan_report(self, toppan_report_pd, toppan_summary_pd):

        local_stamp_total = toppan_summary_pd.loc[toppan_summary_pd['UNIT PRICE'] == 'Local Handling cost','AMOUNT'].values
        oversea_stamp_total = toppan_summary_pd.loc[toppan_summary_pd['UNIT PRICE'] == 'Overseas Handling cost','AMOUNT'].values
        toppan_report_pd['Processing Date and Time'] = pd.to_datetime(toppan_report_pd['Processing Date and Time'])

        toppan_report_pd['circular_pages'] = ((toppan_report_pd['Total Pages']-  toppan_report_pd['(LETTERHEAD)'])/toppan_report_pd['Total Mailset']).astype('int64')

        toppan_report_pd['local_stamp_tabulated'] = np.select(
                                            condlist=[toppan_report_pd['circular_pages'] > 6, toppan_report_pd['circular_pages'] > 2],
                                            choicelist= [0.6,0.37], 
                                            default=0.3)*toppan_report_pd['Local'] 
        toppan_report_pd['oversea_stamp_tabulated'] = np.select(
                                            condlist=[toppan_report_pd['circular_pages'] > 6, toppan_report_pd['circular_pages'] > 2],
                                            choicelist= [1.3,0.9], 
                                            default=0.7)*toppan_report_pd['Oversea']                                             
        toppan_report_pd_sum = toppan_report_pd.sum()
        toppan_report_pd['bw_printing'] = toppan_report_pd['Total Pages']-toppan_report_pd['(LETTERHEAD)']
        toppan_report_pd['local_stamp_bill'] =(toppan_report_pd['local_stamp_tabulated']/toppan_report_pd_sum['local_stamp_tabulated']*local_stamp_total).round(2)
        toppan_report_pd['oversea_stamp_bill'] =(toppan_report_pd['oversea_stamp_tabulated']/toppan_report_pd_sum['oversea_stamp_tabulated']*oversea_stamp_total).round(2)
        billing_item_list = {
                        '(LETTERHEAD)': 16,
                        'bw_printing':15,
                        '(DL)':13,
                        '(C5)':3,
                        '(C4)':2,
                        'local_stamp_bill':41,
                        'oversea_stamp_bill':41
        }

        
        for _,toppan_row in toppan_report_pd.iterrows():
            mcst, type_ref = toppan_row['Filename'].split('-',1)
            for header, usage_type in billing_item_list.items():
                if toppan_row[header]:
                    new_stationary_record = stationary_usage(
                        usage_mcst = mcst,
                        usage_type = usage_type,
                        usage_date = toppan_row['Processing Date and Time'],
                        usage_purpose = f'Toppan Outsource {type_ref}',
                        usage_quantity = toppan_row[header],
                    )
                    db.session.add(new_stationary_record)
                    
        db.session.commit()
        return toppan_report_pd

    def import_all_monthly_report(self):

        report_month_folder =f'{self.report_date.year}\{self.report_date.strftime("%m - %b-%y")}'
        photocopy_initial_folder = 'PHOTOCOPIER FRANKING REPORT\PHOTOCOPIER'
        photocopy_initial_folder = os.path.join(photocopy_initial_folder ,report_month_folder)
        folder_graph = folder_graph_api()

        for filename in folder_graph.get_files_name_in_folder(site_id=folder_graph.invoice_site_id
        , list_id=folder_graph.stationary_list_id,file_path=photocopy_initial_folder):
             photocopy_report_pd = folder_graph.get_file_to_pandas(site_id=folder_graph.invoice_site_id
        , list_id=folder_graph.stationary_list_id, file_path_name= os.path.join(photocopy_initial_folder, filename))
             machine_model = filename.split(" - ")[1].split(".")[0]
             if not self.check_import_record(machine_model):
                self.import_copier_report( photocopy_report_pd=photocopy_report_pd,
                                        machine_model=machine_model)

        franking_initial_folder='PHOTOCOPIER FRANKING REPORT\FRANKING'
        franking_initial_folder=os.path.join(franking_initial_folder,report_month_folder)
        
        
        franking_report_pd = folder_graph.get_lastest_excel_file_to_pandas(site_id=folder_graph.invoice_site_id
        , list_id=folder_graph.stationary_list_id, file_path=franking_initial_folder,search_file_name=".csv") 
        if not self.check_import_record('Franking') and franking_report_pd is not None:  self.import_franking_report(franking_report_pd=franking_report_pd)
        
        
        crimsion_initial_folder=  '99999 - CONSOLIDATION\CRIMSON SEC 47\CRIMSON LOGIC BILLING.xlsx'
        crimsion_report_pd = folder_graph.get_file_to_pandas(site_id=folder_graph.site_id
        , list_id=folder_graph.list_id, file_path_name= crimsion_initial_folder, csv_type =False)
        if not self.check_import_record('Crimsion'):self.import_crimsion_report(crimsion_report_pd=crimsion_report_pd)

        toppan_initial_folder = 'PHOTOCOPIER FRANKING REPORT\OUTSOURCE'
        toppan_initial_folder= os.path.join(toppan_initial_folder, report_month_folder)

        for filename in folder_graph.get_files_name_in_folder(site_id=folder_graph.invoice_site_id
        , list_id=folder_graph.stationary_list_id,file_path=toppan_initial_folder):
            if os.path.splitext(filename)[1] == ".XLSX" : 
                toppan_report_pd = folder_graph.get_file_to_pandas(sheet_name="SMART", header=2, skipfooter=1,site_id=folder_graph.invoice_site_id
        , list_id=folder_graph.stationary_list_id, file_path_name= os.path.join(toppan_initial_folder, filename))                
                toppan_summary_pd = folder_graph.get_file_to_pandas(sheet_name="BILLING SUMMARY", header=21,site_id=folder_graph.invoice_site_id
        , list_id=folder_graph.stationary_list_id, file_path_name= os.path.join(toppan_initial_folder, filename))                
                # toppan_report_pd = pd.read_excel(os.path.join(toppan_initial_folder, filename), 
                #                             sheet_name="SMART", header=2, skipfooter=1)
                # toppan_summary_pd = pd.read_excel(os.path.join(toppan_initial_folder, filename), 
                #                             sheet_name="BILLING SUMMARY", header=21)
                
                if not self.check_import_record('Toppan'):  self.import_toppan_report(toppan_report_pd=toppan_report_pd, toppan_summary_pd=toppan_summary_pd)
    
    def export_monthly_report_pd(self, export_column_list):
        monthly_usage = db.session.query(stationary_usage.usage_mcst, stationary_type.item_group , stationary_type.item_type, 
            db.func.sum(stationary_usage.usage_quantity) , db.func.max(
                stationary_type.item_price), db.func.max(stationary_adjusted_price.item_adjusted_price)).outerjoin(
                stationary_type, stationary_usage.usage_type==stationary_type.id).outerjoin(
                stationary_adjusted_price, 
                (stationary_usage.usage_type == stationary_adjusted_price.item_type) &
                (stationary_usage.usage_mcst == stationary_adjusted_price.item_mcst)).group_by(
                stationary_type.item_type, stationary_usage.usage_mcst , stationary_type.item_group ).filter(
                stationary_usage.usage_date <= self.report_date , 
                stationary_usage.usage_date >=self.report_date.replace(day=1)).all()
        pd_columns= ['mcst', 'item_group', 'item_type', 'quantity', 'default_price','adjusted_price']
        report_pd = pd.DataFrame(monthly_usage, columns=pd_columns)
        report_pd['quantity'] = report_pd['quantity'].round(2)
        report_pd['item_desc'] = report_pd['item_group'] +  " - " + report_pd['item_type']
        report_pd['item_price'] = report_pd.apply(lambda row: row['default_price'] if pd.isnull(row['adjusted_price'])else row['adjusted_price'], axis=1).round(2)
        report_pd['item_billed'] =  report_pd.apply(lambda row: row['quantity'] if pd.isnull(row['item_price']) else row['item_price'] * row['quantity'], axis=1).round(2)
        tabulated_report_pd =  report_pd[export_column_list]
        
        return tabulated_report_pd
   
    def export_file_to_stationary_sharepoint(self, file_name, file, file_ext, file_type):
        result , file_created, file_path = self.folder_graph().upload_new_file(site_id=self.folder_graph().invoice_site_id, list_id=self.folder_graph().stationary_list_id,
        file_path= self.file_path, file=file, file_name=file_name,
        file_type= file_type, file_ext=file_ext)
        return result , file_created
    
    def export_to_excel_report(self):

        export_column_list = ['mcst','item_desc', 'item_billed']
        tabulated_report_pd = self.export_monthly_report_pd(export_column_list)
        pivot_report_pd = tabulated_report_pd.pivot(index="mcst", columns="item_desc", values= 'item_billed')
        total_pivot_report_pd = pivot_report_pd.append(pivot_report_pd.sum().rename('Total Item Billed'))
        total_pivot_report_pd['Total Mcst BIlled'] = total_pivot_report_pd.sum(axis=1)
        report_excel_memory = io.BytesIO()
        total_pivot_report_pd.to_excel(report_excel_memory,float_format="%.2f", freeze_panes=(1,1))
        report_excel_memory.seek(0,0)
        
        file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        file_ext ='xlsx'
        file_name = f'{self.report_date.strftime("%m - STATIONARY BILLING %b-%y").upper()}'
        result ,_ =self.export_file_to_stationary_sharepoint(file_name=file_name,
        file= report_excel_memory.read(), file_ext=file_ext, file_type=file_type)
        return result

    def generate_pdf_breakdown(self , file_path=None):
        PAGE_MARGIN = 15
        BODY_FONT_SIZE= 12
        TABLE_LEFT_MARGIN = 5
        TABLE_COLUMN_WIDTH = 30
        TABLE_COLUMN_WIDTH_DESC = 70
        LINE_BREAK_HEIGHT = 20
        export_column_list = ['mcst','item_desc', 'quantity', 'item_price', 'item_billed']
        report_table_columns = ['item_desc', 'quantity', 'item_price', 'item_billed']
        tabulated_report_pd = self.export_monthly_report_pd(export_column_list)
        mcst_grouped_pd = tabulated_report_pd.groupby('mcst')
        Printing_breakdown_pdf = Printing_breakdown_pdf_class("P", "mm", "A4")
        Printing_breakdown_pdf.set_auto_page_break(auto=True, margin=PAGE_MARGIN)
        Printing_breakdown_pdf.set_font('Arial', 'B', BODY_FONT_SIZE)
        mcst_page_list = []
        for mcst, group in mcst_grouped_pd:
            mcst_detail = smart_project_listing.query.get(mcst)
            Printing_breakdown_pdf.add_page()
            mcst_page_list.append(Printing_breakdown_pdf.page)
            Printing_breakdown_pdf.cell(30,10,f'{mcst} - {mcst_detail.PROPERTY_NAME}')
            Printing_breakdown_pdf.ln(10)
            Printing_breakdown_pdf.cell(30,10,f'Breakdown for the month {self.report_date.strftime("%b-%y")}')
            Printing_breakdown_pdf.ln(20)
            Printing_breakdown_pdf.cell(120)
            Printing_breakdown_pdf.cell(30,10,f'Scan QR for usage Journal')
            Printing_breakdown_pdf.ln(20)

            for index, table_column in enumerate(report_table_columns):    
                Printing_breakdown_pdf.cell(TABLE_LEFT_MARGIN)
                Printing_breakdown_pdf.cell(TABLE_COLUMN_WIDTH_DESC if index== 0 else TABLE_COLUMN_WIDTH,10,table_column,"B")
            Printing_breakdown_pdf.ln(LINE_BREAK_HEIGHT)

            for _ , item_type_detail in group.iterrows():
                for index, table_column in enumerate(report_table_columns):    
                    Printing_breakdown_pdf.cell(TABLE_LEFT_MARGIN)
                    if index== 0:
                        Printing_breakdown_pdf.cell(TABLE_COLUMN_WIDTH_DESC,10,str(item_type_detail[table_column]))
                    else: 
                        Printing_breakdown_pdf.cell(TABLE_COLUMN_WIDTH,10,f'{item_type_detail[table_column]:.2f}')
                Printing_breakdown_pdf.ln(LINE_BREAK_HEIGHT)

            total_billed = group['item_billed'].sum().round(2)
            Printing_breakdown_pdf.cell(80)
            Printing_breakdown_pdf.cell(TABLE_COLUMN_WIDTH,10,"Sub Total", "BT")
            Printing_breakdown_pdf.cell(40)
            Printing_breakdown_pdf.cell(TABLE_COLUMN_WIDTH,10,f'{total_billed:.2f}', "BT")

        printing_bytes = bytearray(Printing_breakdown_pdf.output(None,'S').encode('latin-1'))
        billing_pdf = fitz.open(None, printing_bytes, 'pdf')
        qr_code_rect = fitz.Rect(420, 100, 495, 175)
        crypter= Fernet(os.environ['mcst_key'])

        def add_qr_code_journal(page_index, page_mcst):
            
            mcst_key = crypter.encrypt(str(page_mcst).encode('utf-8')).decode('utf-8')
            qr_code_string = f"https://smartsgportal.azurewebsites.net//#/public/stationaryjournal/{mcst_key}/{self.report_date.strftime('%Y-%m')}"
            qr_code = qr_code_generate_smart(Qrcode_string=qr_code_string)
            billing_page = billing_pdf.loadPage(page_index-1)
            billing_page.insertImage(qr_code_rect, stream=qr_code)
            return page_index, page_mcst
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            mcst_list = [item[0] for item in mcst_grouped_pd['mcst']]
            results = executor.map(add_qr_code_journal,mcst_page_list,mcst_list)
            for result in results: pass
        file_name = f'{self.report_date.strftime("%m - STATIONARY BILLING %b-%y breakdown").upper()}'
        file_ext ='pdf'
        if file_path:
            billing_pdf.save(os.path.join(file_path, f'{file_name}.{file_ext}'))
        else:
            file_type = 'application/pdf'
            
            result ,_ =self.export_file_to_stationary_sharepoint(file_name=file_name,
            file=bytearray(billing_pdf.write()), file_ext=file_ext, file_type=file_type)
            
            print (result)



        return (mcst_grouped_pd['mcst'],printing_bytes)
    
    def combine_invoice_breakdown(self,inv_file_path):
        # breakdown_pages = self.generate_pdf_breakdown(r"C:\Users\Clarence Yeo\Downloads\test.pdf")
        inv_pdf = fitz.open(inv_file_path)
        for inv_page in inv_pdf:
            Invoice_content = inv_page.getText("blocks")
            print (Invoice_content)


class Printing_breakdown_pdf_class (FPDF):

    def header(self):
        HEADER_FONT_SIZE = 15
        HEADER_LEFT_TAB = 35
        SMART_PROPERTY_HQ_INDEX = 8888
        HEADER_TEXT = "Printing and Stationary Reimbursement Breakdown"
        # header_image = open("C:\\Users\\Clarence Yeo\\Smart Property Management (S) Pte Ltd\\SMART HQ ACCOUNTS - SMART HQ ACCOUNTS\\TEMPLATE\\ESTATE LETTERHEAD\\IMAGE HEADER\\8888_SMART PROPERTY HQ.png", 'rb') 
        # mcst_header = mcst_template_header()
        # header_image = mcst_header.get_template_header(SMART_PROPERTY_HQ_INDEX)
        self.set_font('Arial', 'B', HEADER_FONT_SIZE)
        self.cell(HEADER_LEFT_TAB)
        # self.image(header_image,h=70,x=30,y=100,type="png")
        self.cell(w=0, txt=HEADER_TEXT)
        self.ln(20)
        
