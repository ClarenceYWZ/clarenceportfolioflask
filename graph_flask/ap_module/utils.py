import os
import pandas as pd
import keyboard
import time
from datetime import datetime,date
from zipfile import ZipFile
from graph_flask.main.utils import convert_db_to_pandas
from graph_flask.models import smart_project_listing

class mcmanager_extract:

    def __init__(self):
        
        self.mcst_data = convert_db_to_pandas(smart_project_listing)
        self.active_mcsts = self.mcst_data[self.mcst_data.TERMINATED_DATE >= date.today()]

    def add_mcdat_row(self,mcst):
        mcst_name = self.mcst_data[self.mcst_data.PRINTER_CODE == mcst].PROPERTY_NAME.values[0]
        mcdat_str_list= [f'"{format(mcst,"04d")} - {mcst_name}- {module}" "{module}" "MC{mcst}{module}" "MC{mcst}" ' \
                         f'"Z:\MCBACK\MC{mcst}" "{format(mcst,"04d")} - {mcst_name}- GL"'.encode().decode('unicode_escape')
                         for module in ('AP', 'AR', 'GL')]

        return '\n'.join(mcdat_str_list)

    def join_all_mcst_mcdat(self, user):

        if user:
            query_list = smart_project_listing.query.filter(smart_project_listing.TERMINATED_DATE >= date.today(), 
             smart_project_listing.user_list.any(displayname =user)).all()
            mcst_list = [mcst.PRINTER_CODE for mcst in query_list]
        else :
            mcst_list = self.active_mcsts.PRINTER_CODE.sort_values()

        mcst_mcdat_list = [self.add_mcdat_row(active_mcst) for active_mcst in mcst_list]
        all_mcst_mcdat =  '\n'.join(mcst_mcdat_list)
        mcdat_customized_end = '\n'.join(['"Zsystem-10" "Zip Backup" "ZipBACKUP     #backdir\#db.zip    #defdir\#db.*" "" "" ""',
                                '"Zsystem-12" "Zip Restore" "ZipRESTORE    #backdir\#db.zip    #defdir" "" "" "" ',
                                '"Zsystem-30" "Copy Backup" "cCOPY    #fulldb.*     #backdir " "" "" ""',
                                '"Zsystem-32" "Copy Restore" "cRESTORE    #backdir\#db.*    #defdir " "" "" ""',
                                '"Zsystem-40" "Screen Viewer" "" "" "" ""',
                                '"Zsystem-50" "Printer DotMatrix" "" "" "" ""',
                                '"Zsystem-52" "Printer Others Portrait" "" "" "" ""',
                                '"Zsystem-54" "Printer Others Landscape" "" "" "" ""',
                                '"Zsystem-62" "Print Statement Option" "Pre-Printed-Stationery" "" "" ""',
                                '"Zsysz-hid-80" "FileoutAll" "" "" "" "",'])
        return f'{all_mcst_mcdat}\n{mcdat_customized_end}'

    def save_mcdat_file(self, user):
      with open('C:\Mcst10\mc.dat','w') as f:
           f.write(self.join_all_mcst_mcdat(user))

    def get_latest_file(self, mcst, module_type):
        initial_z_folder = r'Z:\MCBACK'
        try:
            search_folder = os.path.join(initial_z_folder,f'MC{mcst}')
            module_files = os.listdir(search_folder)
            match_modules_files = [os.path.join(search_folder,basename) for basename in module_files
                                   if f'MC{mcst}{module_type}' in basename.upper() and os.path.splitext(basename)[1] == '.zip'
                                   and os.path.getsize(os.path.join(search_folder,basename)) > 300000]
            if match_modules_files:
                lastest_file =  max(match_modules_files, key=os.path.getctime)
                return (lastest_file, datetime.fromtimestamp( os.stat(lastest_file).st_mtime))
            else:
                return (None, None)
        except:

            return (None, None)

    def restore_mcst_folder_module(self, mcst, module_type_list):
        restore_record = []
        if type(module_type_list) == str:module_type_list = [module_type_list]
        for module_type in module_type_list:
            latest_file, file_modifed = self.get_latest_file(mcst,module_type)
            extract_path = r'C:\Mcst10' + f'\MC{mcst}'
            if not os.path.isdir(extract_path): os.makedirs(extract_path)
            if latest_file:
                with ZipFile(latest_file,'r') as extract_zip:
                    extract_zip.extractall(path=extract_path)
                restore_record.append((mcst, module_type,file_modifed))
            else:
                restore_record.append((mcst, module_type,None))
        return restore_record

    def restore_mcst_folder(self, mcst):
        module_type_list = ['AP', 'AR', 'GL']
        return self.restore_mcst_folder_module(mcst = mcst, module_type_list=module_type_list)

    def restore_all_files(self):
        self.save_mcdat_file()
        restorelist = [self.restore_mcst_folder(active_mcst) for active_mcst in self.active_mcsts.PRINTER_CODE.sort_values()]
        return (restorelist)

    def get_active_back_up(self):
        restorelist = [[active_mcst, module_type,self.get_latest_file(active_mcst,module_type)[1]] for active_mcst in
                       self.active_mcsts.PRINTER_CODE.sort_values()
                       for module_type in ['AP', 'AR', 'GL']]
        return (restorelist)

    def file_out_ap_listing(self, mcst, month):
        mcst_details = self.active_mcsts[self.active_mcsts.PRINTER_CODE == mcst]
        financial_month = pd.DatetimeIndex(mcst_details.YE).month[0]
        month_diff = month - financial_month
        extract_period = month_diff if month_diff > 0 else 12 + month_diff
        keyboard.wait('m')
        keyboard.press("a")
        keyboard.press("3")
        keyboard.press("F2")
        time.sleep(0.2)
        keyboard.press("F2")
        time.sleep(0.5)
        keyboard.press("f")
        keyboard.press("Enter")
        keyboard.write(f'C:\\Mcst10\\Payment\\08 - AUG-21\\{mcst}-VendorListing202108.txt')
        keyboard.press("Enter")
        time.sleep(0.5)
        keyboard.press("Esc")
        keyboard.press("Esc")
        time.sleep(0.2)
        keyboard.send(f'd, 2, {extract_period}, Enter, Enter, Enter,f, Enter')
        keyboard.write(f'C:\\Mcst10\\Payment\\08 - AUG-21\\{mcst}-paymentListing202108.txt')
        keyboard.press("Enter")
        time.sleep(0.5)
        keyboard.press("Esc")
        keyboard.press("Esc")
        keyboard.send('b, 2')
        for period in range(1,extract_period+1):
            time.sleep(0.3)
            keyboard.send(f'{period}, Enter, Enter, Enter, y, Enter, f, Enter')
            keyboard.write(f'C:\\Mcst10\\Payment\\08 - AUG-21\\{mcst}-invListing2021{period}.txt')
            keyboard.press("Enter")
        keyboard.send("Esc,Esc,Esc")

    def file_out_ap_historical(self, mcback_name,mcst ):
        extract_path= f'C:\Mcst10\{datetime.today().strftime("%Y%m%d")}AP'
        if not os.path.isdir(extract_path): os.makedirs(extract_path)
        time.sleep(0.5)
        keyboard.write(mcback_name)
        time.sleep(0.5)
        keyboard.send("Enter, e, 3")
        keyboard.send("F2, F2, f, Enter")
        print(f'{extract_path}\{format(mcst,"04d")}.txt')
        keyboard.write(f'{extract_path}\{format(mcst,"04d")}.txt')
        keyboard.send("Enter, Esc, Esc, Esc, ?, Backspace, Enter")

    def file_out_all_ap_historical(self, filelist=[]):
        if not filelist:
            filelist = self.get_active_back_up()
        keyboard.send('windows + 7')
        for file in filelist:
            if file[2] and file[1] == "AP" :
                mcst_name = self.mcst_data[self.mcst_data.PRINTER_CODE == file[0]].PROPERTY_NAME.values[0]
                print (f'{format(file[0],"04d")} - {mcst_name}- {file[1]}')
                self.file_out_ap_historical(f'{format(file[0],"04d")} - {mcst_name}- {file[1]}',file[0])

    def input_gl_bf_entry(self,gl_info):
        keyboard.write(gl_info[0])
        keyboard.send("Enter,Enter")
        if len(gl_info) == 3 :
            if gl_info[0][0] in ["6","3","5"] : keyboard.write("-")
            keyboard.write(gl_info[-1])

        keyboard.send("Enter")
        if gl_info[0][0] in ["6","3","5"] : keyboard.write("-")
        keyboard.write(gl_info[-1])
        keyboard.send("Enter")
        if len(gl_info) == 3: keyboard.send("F2")
        for info in gl_info[2:-1]:

            if gl_info[0][0]  in ["6","3","5"]: keyboard.write("-")
            keyboard.write(info)
            keyboard.send("Enter")
        keyboard.send("Enter")

    def input_gl_budget(self,gl_info):
        keyboard.write(gl_info[0])
        keyboard.send("Enter,Enter,Enter")
        if gl_info[0][0] in ["6"] : keyboard.write("-")
        keyboard.write(gl_info[-1])
        keyboard.send("Enter")
        keyboard.send("1,Enter,1,2,Enter,Enter")

    def add_all_account_code(self,acct_info_list):

        keyboard.send("a,1,Enter")
        for info in acct_info_list:
            keyboard.write(info[0])
            keyboard.send("Enter, Enter")
            keyboard.write(info[1])
            keyboard.send("Enter")
            keyboard.send("b") if info[0][0] in ["2","3","5"] else keyboard.send("i")
            keyboard.send("Enter,Enter")
        keyboard.send("Escape,Escape,Escape")

    def add_all_gl_bf_entry(self,mcst_data):
        mcst_data_list = mcst_data.values.tolist()
        self.add_all_account_code(mcst_data_list)

        keyboard.send("b,9")

        for gl_info in mcst_data_list:
            self.input_gl_bf_entry(gl_info)

    def add_all_gl_budget(self,mcst_data):
        mcst_data_list = mcst_data.values.tolist()
        self.add_all_account_code(mcst_data_list)

        keyboard.send("a,5")

        for gl_info in mcst_data_list:
            self.input_gl_budget(gl_info)
    
    def extract_ap_historical(self, historical_text_file):

        colspecs = [(0,11), (11,24),(24,28),(28,37),(37,46),(46,82),(82,95),(95,109),(109,-1)] 
        colNames = ['Supplier', 'Invoice', 'Type', 'Date', 'Due-date','Description', 'Payment-ref', 'amount','net-amount']
        payment_pd = pd.read_fwf(historical_text_file, colspecs=colspecs, names=colNames)
        # return payment_pd
        cond1 = payment_pd['amount'].fillna('').str.contains(r'\d+\-?')
        cond2 = (payment_pd['Description'].fillna('') !='') & (payment_pd['Due-date'].fillna('') == '')
        cond3 = (payment_pd['Supplier'].fillna('').str.contains(r'^\S+[^:]\S+$')) & (payment_pd['Description'].fillna('') == '')
        
        payment_pd = payment_pd[cond1 | cond2 | cond3]
        payment_pd.loc[cond3, 'Supplier'] = payment_pd.loc[cond3,['Invoice','Type','Date','Due-date']].fillna('').agg(''.join, axis=1)
        payment_pd['Supplier'] = payment_pd['Supplier'].ffill()
        payment_pd = payment_pd[~cond3]
        payment_pd['Invoice'] = payment_pd['Invoice'].ffill()
        payment_pd['Type'] = payment_pd['Type'].ffill()
        payment_pd = payment_pd.fillna('')
        payment_pd = payment_pd.groupby(['Supplier','Invoice','Type'])[
            'Date','Due-date','Description','Payment-ref','amount','net-amount'].agg({
                'Description': lambda x :" ".join(x),
                'Date' : lambda x :"".join(x),
                'Due-date' : lambda x :"".join(x),
                'Payment-ref' : lambda x :"".join(x),
                'amount' : lambda x :"".join(x),
                'net-amount' : lambda x :"".join(x),
        })
        payment_pd = payment_pd.reset_index()
        payment_pd[['Date','Due-date']] = payment_pd[['Date','Due-date']].apply(pd.to_datetime)
        invoice_pd = payment_pd.loc[payment_pd['Type'] == "IN"]
        payment_pd = payment_pd.loc[payment_pd['Type'] != "IN"].groupby(['Supplier', 'Payment-ref'])['Invoice', 'Date'].agg({
            'Invoice': lambda x : ','.join(x),
            'Date': lambda x : x,
        })
        return [invoice_pd,payment_pd]
    


if __name__ == "__main__":
    # mcst_data = pd.read_excel(r"C:\Users\Clarence Yeo\Smart Property Management (S) Pte Ltd\SMART HQ ACCOUNTS - SMART HQ ACCOUNTS\2759 - MEDON SPRING\STARTUP\STRATA ROLL\ImpSPMast1.xlsx").replace("-",0).fillna("").round(2)
    mcst_data = pd.read_excel(
        r"C:\Users\Clarence Yeo\Documents\testing\2759.xlsx")
    # mcst_data['DATE'] = mcst_data['DATE'].dt.strftime('%d/%m/%y')
    mcst_data['ACCOUNT'] = mcst_data['ACCOUNT'].astype(str)
    testing_extract = mcmanager_extract()
    
    keyboard.wait('Left')
    # testing_extract.add_all_gl_budget(mcst_data)
    # testing_extract.input_ar_inv_previous_month(mcst_data.values.tolist())
    # keyboard.send("b,9")


    for inv_info in mcst_data.values.tolist():
        print(inv_info)
    #     # print (inv_info[0][0]=="6" ,inv_info[1:-1],inv_info[-1] )
    #     testing_extract.input_ar_receipt_current_month(inv_info)
        testing_extract.amend_ar_code_strata (inv_info[0],inv_info[1])



