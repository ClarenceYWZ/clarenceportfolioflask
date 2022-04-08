from datetime import datetime
from graph_flask.ar_module.utils import ar_graph_api
from graph_flask.printing_postage.utils import printing_class
from dateutil.relativedelta import relativedelta
from flask import request


def invoicepaynowGenerate(request_file):
    
    folder_graph = ar_graph_api()
    try :
        _ , file_name_ext, file_path = folder_graph.upload_new_invoice_file(request_file.read())
        return {'result': f'paynow invoice successfully created -> {file_path}\{file_name_ext}'}
    except :
        return {'error' : f'Please check on the upload billing file'}


def printing_postage_report_generate (report_month): 

    try :
        report_date = datetime.strptime(report_month, "%Y-%m")  + relativedelta(months =1 , days =-1)
        printing_cls = printing_class(report_date=report_date)
        printing_cls.import_all_monthly_report()
        printing_cls.export_to_excel_report()
        printing_cls.generate_pdf_breakdown()
        return {'result': f'Printing Postage report successfully created -> {report_date.strftime("%b-%Y")}'}
    except : 
        return {'error' : f'Unknown Error, error report send to Developer'}