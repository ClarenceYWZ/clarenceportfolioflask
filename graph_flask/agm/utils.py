
from graph_flask import config, db ,mail
import uuid
import pandas as pd
import os
import numpy as np
from flask import render_template
from flask_mail import Message
from graph_flask.models import smart_project_listing
import random
import string,requests

def randomString(stringLength):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(stringLength))


def send_agm_instruction_email(listing_spreadsheet):
    list_csv = pd.read_excel(listing_spreadsheet)
    list_csv['password'] = [randomString(8) for i in range(len(list_csv.index))]
    list_csv[['first_name','last_name']] = list_csv['Name'].str.split(expand=True)
    list_csv['prefix'] =list_csv['sp_id']
    list_csv['user_name'] =list_csv['sp_id']
    lumi_csv = list_csv[['user_name','password','prefix','first_name','last_name','shares']]

    lumi_csv.to_csv(r'C:\Users\Clarence Yeo\OneDrive - Smart Property Management (S) Pte Ltd\PRESENTATION\VIRTUAL AGM\ROOTSASIA\UPLOAD\Lumi AGM Mobile - Participant Upload File - 893550461.csv', index=False)
    for index, userrow in list_csv.iterrows():
        msg = Message(f' Virtual AGM login ',
                      sender=os.environ.get('EMAIL_USER'),
                      recipients=[userrow.Email]
                      )


        footimage_folder = r'C:\Users\Clarence Yeo\Smart Property Management (S) Pte Ltd\SMART HQ ACCOUNTS - SMART HQ ACCOUNTS\TEMPLATE\ESTATE LETTERHEAD\IMAGE HEADER'
        msg.attach(filename='footerimage.png', content_type='image/png',
                   data=open(os.path.join(footimage_folder, 'CLARENCE_EMAIL_FOOTER.png'), 'rb').read(),
                   disposition='inline',
                   headers=[['Content-ID', '<Myimage>'], ])
        msg.html = render_template('agm/agm_instruction_email.html', user =userrow)

        mail.send(msg)
    return msg.html

def globino_delete_user(user_id):
    globino_session = requests.session()
    globinio_login = {
        'email': 'admin@smart.com',
        'password': '1Qaz,xsW2'

    }
    with globino_session as s:
        s.post(url="https://www.cococo.ai/Admin/Login/Index",data=globinio_login)
        try:
            s.delete(f'https://www.cococo.ai/api/ParticipantsAdmin/{user_id}')
        except:
            print (user_id)



