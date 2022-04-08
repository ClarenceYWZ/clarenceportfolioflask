from datetime import datetime
import keyboard
import time
import pyqrcode
import fitz
import re
import numpy as np
import pandas as pd
import io,os,time
import secrets
import concurrent.futures
from graph_flask.microsoft.utils import folder_graph_api
# from PyPDF2 import PdfFileReader
from graph_flask.models import smart_project_listing
from graph_flask.ap_module.utils import mcmanager_extract
from flask import url_for
from PIL import Image
import pycrc.algorithms


def qr_code_generate_smart(Qrcode_string, logo_file=None, logo_size = 180, module_color = "#000000"):

    url = pyqrcode.create(Qrcode_string,error = 'H')
    img_io = io.BytesIO()
    url.png(img_io,scale=10, module_color=module_color )
    img = Image.open(img_io)
    img = img.convert("RGBA")
    width,_ = img.size

    # How big the logo we want to put in the qr code png

    # Open the logo image
    if not logo_file:
        logo_file = Image.open(os.path.abspath('graph_flask/static/images/favicon.ico'),'r').convert("RGBA")
        

    # Calculate xmin, ymin, xmax, ymax to put the logo
    xmin = ymin = int((width / 2) - (logo_size / 2))
    xmax = ymax = int((width / 2) + (logo_size / 2))

    # resize the logo as calculated
    logo_file = logo_file.resize((xmax - xmin, ymax - ymin))

    # put the logo in the qr code
    img.paste(logo_file, (xmin, ymin, xmax, ymax))
    img.thumbnail((150,150))

    b = io.BytesIO(img.tobytes())

    img.save(b,'png')
    img.close()
    print ('generated ', Qrcode_string)
    return b

def paynow_qrcode(PayNow_ID, Merchant_name, Bill_number, Transaction_amount,Paynow_logo):

    # time.sleep(1)
    # module from https://pycrc.org

    Can_edit_amount = "0"
    Merchant_category = "0000"
    Transaction_currency = "702"
    Country_code = "SG"
    Merchant_city = "Singapore"
    Globally_Unique_ID = "SG.PAYNOW"
    Proxy_type = "2"

    start_string = "010212"
    Dynamic_PayNow_QR = "000201"
    Globally_Unique_ID_field = "00"
    Globally_Unique_ID_length = str(len(Globally_Unique_ID)).zfill(2)
    Proxy_type_field = "01"
    Proxy_type_length = str(len(Proxy_type)).zfill(2)
    PayNow_ID_field = "02"
    PayNow_ID_Length = str(len(PayNow_ID)).zfill(2)
    Can_edit_amount_field = "03"
    Can_edit_amount_length = str(len(Can_edit_amount)).zfill(2)
    Merchant_category_field = "52"
    Merchant_category_length = str(len(Merchant_category)).zfill(2)
    Transaction_currency_field = "53"
    Transaction_currency_length = str(len(Transaction_currency)).zfill(2)
    Merchant_Account_Info_field = "26"
    Merchant_Account_Info_length = str(len(Globally_Unique_ID_field + Globally_Unique_ID_length + Globally_Unique_ID + \
                                           Proxy_type_field + Proxy_type_length + Proxy_type + \
                                           PayNow_ID_field + PayNow_ID_Length + PayNow_ID + \
                                           Can_edit_amount_field + Can_edit_amount_length + Can_edit_amount)).zfill(2)

    Transaction_amount_field = "54"
    Transaction_amount_length = str(len(Transaction_amount)).zfill(2)
    Country_code_field = "58"
    Country_code_length = str(len(Country_code)).zfill(2)
    Merchant_name_field = "59"
    Merchant_name_length = str(len(Merchant_name)).zfill(2)
    Merchant_city_field = "60"
    Merchant_city_length = str(len(Merchant_city)).zfill(2)
    Bill_number_field = "62"
    Bill_number_sub_length = str(len(Bill_number)).zfill(2)
    Bill_number_length = str(len("01" + Bill_number_sub_length + Bill_number)).zfill(2)

    data_for_crc = Dynamic_PayNow_QR + start_string + Merchant_Account_Info_field + Merchant_Account_Info_length + \
                   Globally_Unique_ID_field + Globally_Unique_ID_length + Globally_Unique_ID + \
                   Proxy_type_field + Proxy_type_length + Proxy_type + \
                   PayNow_ID_field + PayNow_ID_Length + PayNow_ID + \
                   Can_edit_amount_field + Can_edit_amount_length + Can_edit_amount + \
                   Merchant_category_field + Merchant_category_length + Merchant_category + \
                   Transaction_currency_field + Transaction_currency_length + Transaction_currency + \
                   Transaction_amount_field + Transaction_amount_length + Transaction_amount + \
                   Country_code_field + Country_code_length + Country_code + \
                   Merchant_name_field + Merchant_name_length + Merchant_name + \
                   Merchant_city_field + Merchant_city_length + Merchant_city + \
                   Bill_number_field + Bill_number_length + "01" + Bill_number_sub_length + Bill_number + \
                   "6304"

    

    # Sample code from https://pycrc.org
    crc = pycrc.algorithms.Crc(width=16, poly=0x1021,
                               reflect_in=False, xor_in=0xffff,
                               reflect_out=False, xor_out=0x0000)

    my_crc = crc.bit_by_bit_fast(data_for_crc)  # calculate the CRC, using the bit-by-bit-fast algorithm.
    crc_data_upper = ('{:04X}'.format(my_crc))


    final_string = data_for_crc + crc_data_upper
    
    return qr_code_generate_smart(final_string,Paynow_logo, logo_size=200, module_color="#7C1A78")

def input_paynow_code(file_path,inv_type = "MCMANAGER"):

    INVOICE_DATE_X0 = 400
    INVOICE_DATE_Y0 = 160
    INVOICE_DATE_X1 = 500
    INVOICE_DATE_Y1 = 180
    PAYMENT_ADVICE_X0 = 100
    PAYMENT_ADVICE_Y0 = 600
    PAYMENT_ADVICE_X1 = 800
    PAYMENT_ADVICE_Y1 = 800

    search_date_rect = fitz.Rect(INVOICE_DATE_X0,INVOICE_DATE_Y0,INVOICE_DATE_X1,INVOICE_DATE_Y1)
    search_payment_adv_rect = fitz.Rect(PAYMENT_ADVICE_X0,PAYMENT_ADVICE_Y0,PAYMENT_ADVICE_X1,PAYMENT_ADVICE_Y1)

    if type(file_path) == str :
        billing_pdf = fitz.open(file_path)
    else :
        billing_pdf = fitz.open(None, file_path, 'pdf')
    main_page = billing_pdf.loadPage(0)
    Invoice_content = main_page.getText("blocks")
    
    Paynow_logo_file =  f'{os.getcwd()}/graph_flask/static/images/PAYNOW_LOGO.png'
    Paynow_logo = Image.open(Paynow_logo_file, 'r')
    inv_type= str(inv_type).upper()
    
    if inv_type == 'MCMANAGER':
        qr_code_rect = fitz.Rect(520, 670, 595, 745)
    else:
        qr_code_rect = fitz.Rect(480, 675, 555, 750)

    for block_content in Invoice_content:

        if "PLAN NO." in block_content[4]:
            
            Search_string= re.search(r"\.*\s+(PLAN NO\.\s+)?(\d+)" , block_content[4])

            mcst_info= smart_project_listing.query.filter(smart_project_listing.PRINTER_CODE == Search_string.group(2)).first()
            paynow_id = mcst_info.paynow_list.paynow_uen
                    
            break
    
    date_search_blocks = main_page.getTextWords(search_date_rect)        
    for block in date_search_blocks :
        Search_string = re.search(r'\.*(\d\d/\d\d/\d+)\.*', block[4])
        if Search_string : 
            invoice_date = datetime.strptime(Search_string.group(1),"%d/%m/%Y")
            break
    

    max_page = billing_pdf.pageCount
    
    def addQrcodetoPage(pdf_page):

        Invoice_page = billing_pdf.loadPage(pdf_page)
        Invoice_content = Invoice_page.getTextbox(search_payment_adv_rect)
        # return Invoice_content
        
        # for block_content in Invoice_content:
        try:
            if inv_type == 'MCMANAGER':
        
                Search_string = re.search(
                    r"\s*([a-zA-z0-9]+\-[a-zA-z0-9]+\-[a-zA-z0-9]+)[\s\r\n]+(\d\d/\d\d/\d\d\d\d)[\s\r\n]+(\S+)",
                    Invoice_content)
                    
                if not Search_string is None:
                    UNIT_ACCOUNT_NO = Search_string.group(1)
                    amount_due = Search_string.group(3).replace(",", "").replace("NA", '0')
            

            else:
                if "UNIT ACCOUNT NO. :" in block_content[4]:
                    Search_string = re.search(r"\.*(UNIT ACCOUNT NO. :)\s+(\S+)", block_content[4])
                    UNIT_ACCOUNT_NO = Search_string.group(2)
            
                if "Total Due:" in block_content[4]:
                    Search_string = re.search(r"\.*(Total Due:)\s+\$(\S+)", block_content[4])
                    amount_due = Search_string.group(2)
        except:

            print(f'{pdf_page} error printing')

        if not UNIT_ACCOUNT_NO == "":
            
            
            paynow_qr = paynow_qrcode(f'{paynow_id}', f"MCST PLAN NO.{mcst_info.MCST_no}", UNIT_ACCOUNT_NO,
                                      amount_due.replace(",", ""),Paynow_logo)

            
            Invoice_page._cleanContents()
            if not Invoice_page._wrapContents():
                Invoice_page.wrapContents()

            Invoice_page.insertImage(qr_code_rect, stream=paynow_qr)
            
            UNIT_ACCOUNT_NO = ""


    with concurrent.futures.ThreadPoolExecutor() as executor:
        pdf_pages = [*range(0, max_page)]
        # pdf_pages = [9,10]
        executor.map(addQrcodetoPage,pdf_pages)



    name , ext = os.path.splitext(file_path)
    if type(file_path) == str:billing_pdf.save(f'{name}(Qr code){ext}', deflate= True)
        # billing_pdf.close()
    return mcst_info, io.BytesIO(billing_pdf.write()) ,invoice_date


class ar_graph_api(folder_graph_api):

    def upload_new_invoice_file(self, invoice_file):
        mcst_info, billing_pdf,invoice_date = input_paynow_code(invoice_file)
        
        file_path = f'{mcst_info.PRINTER_CODE:04d} - {mcst_info.PROPERTY_NAME}\Billing\Billing Invoices' \
                    f'\{invoice_date.year:04d}'

        quarter_end =  pd.Timestamp(invoice_date) + pd.DateOffset(months = 3 , days = -1)                    
        file_name = f'{pd.Timestamp(invoice_date).quarter:02d} - MCST {mcst_info.PRINTER_CODE:04d} BILLING '\
                    f'INVOICE {invoice_date.strftime("%b-%y")} - {quarter_end.strftime("%b-%y")} (QR Code)'.upper()  
        result = self.upload_new_file(self.site_id, self.list_id, file_path,billing_pdf,file_name , "application/pdf", 'pdf')
        return result


class ar_mcmanager_extract(mcmanager_extract):
    
    def amend_ar_strata_address(self, unit, mailing_address):
        keyboard.write(unit)
        for _ in range(7) : keyboard.send("Enter")
        for mailing_address_line in mailing_address:
            if mailing_address_line:
                keyboard.write(mailing_address_line)
                keyboard.send("Enter")
        keyboard.send("F2, F2, ENTER")

    def amend_ar_code_strata(self, unit, outstanding_amt):
        keyboard.write(unit)
        for _ in range(28) : keyboard.send("Enter")
        keyboard.write("2110")
        time.sleep(0.3)
        print (outstanding_amt > 0)
        if outstanding_amt > 0 : keyboard.send("F2, Left, ENTER")
        keyboard.send("F2, F2, ENTER")

    def amend_ar_code_strata_with_arrear(self,unit):
        keyboard.write(unit)
        for _ in range(28) : keyboard.send("Enter")
        keyboard.write("2110")
        time.sleep(0.3)
        keyboard.send("F2, Left, Enter, Space, Enter")

    def input_ar_inv_previous_month(self,inv_info):
        for info in inv_info:
            keyboard.write(info)
            keyboard.send("Enter")
        keyboard.send("Left, Enter")

    def input_ar_receipt_previous_month(self,inv_info):
        
        keyboard.write(inv_info[0])
        keyboard.send("Enter, Enter")
        for info in inv_info[1:]:
            keyboard.write(info)
            keyboard.send("Enter")
        keyboard.send("Left, Enter, Esc, 3, Enter, Enter, 1, Enter")

    def input_adj_last_inv(self,inv_info,inv_relative_pos_last_row = 0):
        
        time.sleep(0.3)
        for info in inv_info:
            if info: keyboard.write(info)
            keyboard.send("Enter")
        keyboard.send("End")
        
        for _ in range(inv_relative_pos_last_row) : keyboard.send("Up")
        for _ in range(4) : keyboard.send("Enter")
        keyboard.send("Esc, 1, Enter")

    def input_ar_receipt_current_month(self,inv_info):
        keyboard.send("Enter")
        keyboard.write(inv_info[0])
        keyboard.send("Enter, Enter")
        for info in inv_info[1:]:
            keyboard.write(info)
            keyboard.send("Enter")
        for _ in range(1,15) : keyboard.send("Enter")
        keyboard.send("Esc, 3, Enter, Enter, 1, Enter")

    def input_ar_prepay_offset(self,inv_info):
        keyboard.send("Enter")
        keyboard.write(inv_info[0])
        for _ in range(0,5): keyboard.send("Enter")
        keyboard.write("PREPAY OFFSET")
        for _ in range(0,7):keyboard.send("Enter")
        keyboard.send("Esc, 1, Enter")

    def file_out_ar_listing(self, mcst):

        keyboard.press("a")
        keyboard.press("3")
        keyboard.press("F2")
        time.sleep(0.2)
        keyboard.press("F2")
        time.sleep(0.5)
        keyboard.press("f")
        keyboard.press("Enter")
        keyboard.write(f'C:\\Mcst10\\SP LISTING\\08 - AUG-21\\{mcst}-202108.txt')
        keyboard.press("Enter")
        time.sleep(0.5)
        keyboard.press("Esc")
        keyboard.press("Esc")
        time.sleep(0.2)
        keyboard.press("Esc")

    def extract_all_ar_listing(self, extract_list):
        keyboard.send('windows+7')
        time.sleep(3.5)
        keyboard.press('down')
        keyboard.press('home')
        for extract_item in extract_list:
            time.sleep(0.4)
            if extract_item[2] and extract_item[1] =="AR":
                print(extract_item)
                time.sleep(0.5)
                keyboard.press('Enter')
                self.file_out_ar_listing(extract_item[0])
            keyboard.press('Down')

    def extract_ar_strata(self, strata_text_file):

        colspecs = [(0,14), (14,25),(25,62),(62,94),(94,-1)] 
        colNames = ['account-no', 'field-name', 'field-value', 'static-details', 'financial-details']
        strata_pd = pd.read_fwf(strata_text_file, colspecs=colspecs, names=colNames)
        strata_pd = strata_pd.dropna(subset=['field-value','static-details'], how="all")
        strata_pd['account-no'] = strata_pd['account-no'].fillna('').replace(' ', '', regex=True)
        strata_pd['static-details'] = strata_pd['static-details'].fillna('')
        strata_pd['field-value'] = strata_pd['field-value'].fillna('')
        strata_pd['field-name'] = strata_pd['field-name'].replace('Address', '',regex=True).fillna('')
        # remove non account format XX-XX-XXX or empty string 
        
        strata_pd =strata_pd[
            (strata_pd['account-no'].str.contains(r'([\w\s]{3}-[\w\s]{2}-[\w\s])|^(?![\S\s])') )& 
            (strata_pd['field-value'] != 'AR - SUB-PROPRIETOR')]
        strata_pd['account-no'] = strata_pd['account-no'].replace(r'^\s*$', np.nan, regex=True).ffill()
        strata_pd['field-name'] = strata_pd['field-name'].replace(r'^\s*$', np.nan, regex=True).replace(
                                    ':','',regex=True).ffill()
        
        # combine additional name col value 
        mask = strata_pd['field-name'] == "Add.Names"
        strata_pd.loc[mask, 'field-value'] = strata_pd.loc[mask, ['field-value','static-details']].agg(''.join, axis=1)
        strata_pd.loc[mask, 'static-details'] =":"
        strata_pd[["static-field-name", "static-field-value"]] = pd.DataFrame(strata_pd['static-details'].str.split(":",1).tolist(), index= strata_pd.index)
        strip_column_list = ["static-field-name", "static-field-value","field-name","field-value"]
        strata_pd[strip_column_list]=strata_pd[strip_column_list].apply(lambda x : x.str.strip())
        
        strata_static_pd = strata_pd.drop(columns=['field-name','field-value']).rename(columns={'static-field-name':'field-name',	 
                'static-field-value':'field-value'})
        strata_pd = strata_pd.append(strata_static_pd)
        strata_pd = strata_pd.dropna(subset=['field-value'], how="all")
        strata_pd['field-value'] = strata_pd['field-value'].apply(str)
        strata_pd = strata_pd.fillna('')

        strata_pd = strata_pd.groupby(['account-no', 'field-name'], as_index=False).agg({'field-value': ' '.join})
        strata_pd = strata_pd.pivot(index="account-no", columns="field-name", values= "field-value").fillna("")                
        return strata_pd
        
    def extract_ar_user_list(self, strata_text_file) :
        strata_pd = self.extract_ar_strata(strata_text_file)
        strata_pd = strata_pd[strata_pd.columns.intersection(['account-no', 'BlkUnit', 'Contact','Email','Fax','Mailing',
            'Add.Names', 'Name[1]', 'Name[2]'])] 
        id_vars= ['account-no', 'BlkUnit', 'Contact','Email','Fax','Mailing']
        value_vars = ['Add.Names', 'Name[1]', 'Name[2]']
        strata_pd.reset_index(level=0, inplace=True)
        strata_pd= pd.melt(strata_pd, id_vars=id_vars,value_vars=value_vars)
        strata_pd = strata_pd[strata_pd['value'] != ""]
        return strata_pd

    def extract_ar_detailed_fund(self, detailed_fund_file):
        colspecs = [(0,12), (12,48),(48,53),(53,74),(74,83),(83,86),(86,95),(95,109),(109,-1)] 
        colNames = ['account-no', 'sp-name', 'item-type', 'item-desc','inv-id', 'inv-type', 'item-date', 'item-amt', 'item-tot-amt']
        detailed_fund_pd = pd.read_fwf(detailed_fund_file, colspecs=colspecs, names=colNames, thousands=',')
        detailed_fund_pd = detailed_fund_pd.dropna(subset=['item-amt'])
        detailed_fund_pd = detailed_fund_pd[detailed_fund_pd['item-amt'].str.contains(r'^\d+')]
        detailed_fund_pd = detailed_fund_pd.ffill()
        detailed_fund_pd['item-date'] = pd.to_datetime(detailed_fund_pd['item-date'], format="%d/%m/%y")
        detailed_fund_pd['item-amt'] = detailed_fund_pd['item-amt'].astype(float)
        return detailed_fund_pd
    
    def extract_ar_prepay(self, detailed_fund_file):
        colspecs = [(0,12), (12,48),(48,57),(57,60),(60,69),(69,83),(83,98),(98,-1)] 
        colNames = ['account-no', 'sp-name', 'item-code', 'inv-id', 'item-date', 'item-amt', 'item-tot-amt', 'item-os']
        detailed_fund_pd = pd.read_fwf(detailed_fund_file, colspecs=colspecs, names=colNames, thousands=',')
        detailed_fund_pd = detailed_fund_pd.dropna(subset=['item-amt'])
        detailed_fund_pd = detailed_fund_pd[detailed_fund_pd['item-amt'].str.contains(r'^\d+\.\d\d-')]
        detailed_fund_pd = detailed_fund_pd.ffill()
        detailed_fund_pd['item-date'] = pd.to_datetime(detailed_fund_pd['item-date'], format="%d/%m/%y")
        detailed_fund_pd['item-amt'] = detailed_fund_pd['item-amt'].apply(lambda x : x.replace('-',"")).astype(float)
        return detailed_fund_pd
    

if __name__ == "__main__":
     # paynow_qrcode('S98MC2189C','MCST PLAN NO. 2189','001-02-05','100.23')
    # billing_pdf = fitz.open(r"C:\Users\Dreamcore RTS\Smart Property Management (S) Pte Ltd\SMART HQ ACCOUNTS - SMART HQ ACCOUNTS\4593 - WANDERVALE\INVOICES\BILLING INVOICES\2020\03 - MCST 4593 WANDERVALE BILLING INVOICE JUL'20 - SEP'20.pdf")

    input_paynow_code(r"C:\Users\Dreamcore RTS\Smart Property Management (S) Pte Ltd\SMART HQ ACCOUNTS - SMART HQ ACCOUNTS\4593 - WANDERVALE\INVOICES\BILLING INVOICES\2021\01 - MCST 4593 WANDERVALE BILLING INVOICE JAN'21 - MAR'21.pdf",inv_type= "smartyware")