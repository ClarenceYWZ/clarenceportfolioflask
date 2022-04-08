import csv
from datetime import datetime,timedelta
import requests
import re
import os
# import html5lib
from bs4 import BeautifulSoup
from sqlalchemy import desc

headers = {
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

class reallySg:
    url = 'https://rails-hasura-production-api.really.sg/graphsql'
    session =  requests.session()
    def __init__(self):
        self.data ={
            "email": "Clarence.yeo@smartproperty.sg",
            "password": "xxxxxx",
               }
        self.apiUrl = "https://rails-hasura-production-api.really.sg/graphql"


    def getVendorList(self):
        data = {
            'query':  "\n        query ($limit: Int!, $offset: Int!, $search: String!, $company_ids: [uuid!], $label_ids: [uuid!], $category_ids: [uuid!]) {\n          companies(order_by: {name: asc}, limit: $limit, offset: $offset, where: {_and: [{name: {_ilike: $search}}], company_categories: {category_id: {_in: $category_ids}}, id: {_in: $company_ids}}) {\n            id\n            name\n            email\n            phone\n            uen\n            address\n            status\n            contact_person_id\n            vendor_contracts{\n              id\n              status\n              name\n            }\n            contact_person {\n              first_name\n              last_name\n            }\n            company_labels(where: {label_id: {_in: $label_ids}}) {\n              id\n              label_id\n              company_id\n            }\n            company_categories {\n              category {\n                id\n                name\n              }\n            }\n          }\n          companies_aggregate(where: {_and: [{company_categories: {category_id: {_in: $category_ids}}, name: {_ilike: $search}}], id: {_in: $company_ids}}) {\n            aggregate {\n              count\n            }\n          }\n        }\n      ",
            'variable': '{ "limit": 10,  "offset": 0,  "search": "%%"}'
            }
        vendorList = requests.post(self.apiUrl,data=data)
        print (vendorList.text)
    def extractVendorList(self,htmlString,outputFilePathName):
        soup = BeautifulSoup(htmlString,'html.parser')


        with open(outputFilePathName, 'w', encoding="utf-8", newline='') as csv_file:
            csvWriter = csv.writer(csv_file)
            for tbody in soup.find_all('tbody'):
                for index,tr in enumerate(tbody.find_all('tr')):
                    row_value = []

                    for index, td in enumerate(tr.find_all('td')):
                        value= td.getText().rstrip()
                        print(value)
                        try:
                            row_value.append(value)
                        except:
                            row_value.append("")
                    print(row_value)
                    csvWriter.writerow(row_value)
    
    def extract_seabridge_dashboard(self, htmlString, outputfilepathname):
       
        soup = BeautifulSoup(htmlString, 'html.parser')
        with open(outputfilepathname, 'w', encoding='utf-8', newline='') as csv_file:
            csvWriter = csv.writer(csv_file)
            row_value= ['Vendor', 'Inv', 'Inv$','Budget', 'po-date', 'inv-due-date', 'match', 'pending with','status', 'inv-desc']
            for div in soup.find_all('div'):
                if div.attrs.get('class'):
                    if div.attrs.get('class')[0] == 'dashboard-list-item' : 
                        csvWriter.writerow(row_value)
                        row_value = []
                        
                if div.getText() and div.attrs.get('class'): 
                    if not div.attrs.get('class')[0] in ['row','result','dashboard-list-item']: 
                        print (div.attrs.get('class'))
                        row_value.append(div.getText())


if __name__ == '__main__':
    test = reallySg()
    print(test.url)
    test.test()
    
