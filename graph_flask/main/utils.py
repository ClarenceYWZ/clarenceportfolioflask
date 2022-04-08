from graph_flask import  db
import json
import requests
import pandas as pd
from flask import jsonify
# from graph_flask import requests_session
from graph_flask.models import smart_project_listing

from datetime import datetime
import random
import string

def randomString(stringLength):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(stringLength))

def update_sql_json(sql_object, request_value):
     for data_item in request_value:
        if hasattr(sql_object, data_item) and type(request_value[data_item]) in [str, int, float, bool] :
            if "DATE" in data_item.upper() : 
                if "GMT" in str(request_value[data_item]):
                    data_value = datetime.strptime(str(request_value[data_item]), "%a, %d %b %Y %H:%M:%S %Z")
                elif "T" in str(request_value[data_item]) : 
                    data_value = datetime.strptime(str(request_value[data_item]), "%Y-%m-%dT%H:%M:%S.%fZ")
                elif "/" in str(request_value[data_item]):
                    data_value = datetime.strptime(str(request_value[data_item]), "%d/%m/%Y")
                else : 
                    data_value = datetime.strptime(str(request_value[data_item]), "%Y-%m-%d")
            else :
                data_value =  request_value[data_item]

            sql_object.__setattr__(data_item, data_value)

def jsonify_api_headers(jsonfiy_object):
    response = jsonify(jsonfiy_object)
    
    return response

def import_excel_to_db(spreadsheet_path, database_model = None , col_astype = {} ):
    list_csv = pd.read_excel(spreadsheet_path, parse_dates=True, dtype=col_astype).fillna('')
    
    for post_item in list_csv.to_dict('records'):

        database_entry = database_model(**post_item)
        db.session.add(database_entry)
    db.session.commit()

def getMcstDetails(mcstNo):
    url = f'https://data.gov.sg/api/action/datastore_search?resource_id=21b15082-ea01-40f8-ad2b-679f011d6764&q={mcstNo}'
    result = json.loads(requests.get(url).text)
    if result['result']['records']:
         for record_item in result['result'] ['records'] : 
             if record_item['usr_mcno'] == str(mcstNo) : return record_item
    else:
        return []

def getMcstGstReg(Uen_no):
    client_id = '3c57f9e2-1665-43c2-a9ac-2edd1424f9de'
    client_secret = 'T0rC5oG6uL8iX4yE7bC4lM5vT1xL8uJ8eL0aI3iV4aY6iC5jK5'
    url = f'https://apiservices.iras.gov.sg/iras/prod/GSTListing/SearchGSTRegistered'
    # client_id = '77c8cb49-b911-42e4-b15f-599345a50bdb'
    # client_secret = 'U2iR3eQ4rS8sX7jD4cX7mT5sQ0nH5dV8nU3oD7sV1hD3cO4yX5'
    # url = f'https://apisandbox.iras.gov.sg/iras/sb/GSTListing/SearchGSTRegistered'
    headers = {
        "X-IBM-Client-Id": client_id,
        "X-IBM-Client-Secret": client_secret,
        "accept": "application/json",
        "content-type": "application/json"
    }

    data= {
        "clientID": client_id,
        "regID":  Uen_no
    }
    print (json.dumps(data))
    result = eval(requests.post(url, headers=headers, data=json.dumps(data)).text)
    return result

def convert_db_to_pandas(database_model):

    query_obj = database_model.query.all()
    return pd.DataFrame([item.to_json() for item in query_obj])


if __name__ =='__main__':
    import_excel_to_db(r"Z:\ACCOUNTS\9999 - CONSOLIDATION\OTHERS\PROJECT_LISTING.xlsx", smart_project_listing)


