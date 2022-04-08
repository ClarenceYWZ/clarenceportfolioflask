import requests
# from rauth import OAuth2Service
# import html5lib
from bs4 import BeautifulSoup
from flask import session
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

import json
import graph_flask.config as config
from flask import redirect,url_for,request,Request

headers = {
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

class zoom_api:


    def __init__(self):
        self.access_token = None
        self.client_id = config.zoom_client_id
        self.client_secret = config.zoom_client_secret
        self.redirect_uri = 'https://smartpropertyportal.azurewebsites.net/zoomredirect'
        # self.authorize_uri = f'https://zoom.us/oauth/authorize?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}'
        self.authorize_uri = f'https://zoom.us/oauth/authorize'
        self.api_uri= 'https://api.zoom.us/v2'
        self.token_uri=f'https://zoom.us/oauth/token'
        # self.scope = ['ruser:master meeting:write:admin meeting:read:admin account:write:admin user:write:admin recording:write:admin']
        self.auth = HTTPBasicAuth(self.client_id, self.client_secret)
        self.client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=self.client)
        self.access_token = self.oauth.fetch_token(token_url=self.token_uri,auth=self.auth)

        print (self.access_token)
        # refresh_token = requests.post(f'{self.token_uri}/refresh_token={self.access_token["access_token"]}&grant_type=refresh_token')
        # print(refresh_token)
        self.headers = {'Authorization': 'Bearer ' + self.access_token['access_token']}

    def get_zoom_api(self, zoom_path):


        zoom_data = requests.get(
            zoom_path,
            headers=self.headers,
        ).json()

        return zoom_data

    def post_zoom_api(self, zoom_path, json_required):
        # json_required['Authorization']= 'Bearer ' + self.token['access_token']
        self.headers['Content-type'] = 'application/json'
        zoom_data = requests.post(  # Use token to call downstream service
            zoom_path,
            headers=self.headers,
            data=json.dumps(json_required)
        ).json()
        return zoom_data

    def patch_zoom_api(self, zoom_path, json_required={}):
        # json_required['Authorization']= 'Bearer ' + self.token['access_token']
        data = json.dumps(json_required)
        self.headers['Content-type'] = 'application/json'

        requests.patch(  # Use token to call downstream service
            zoom_path,
            headers=self.headers,
            data=data
        )

    def get_all_user(self):
        # zoom_path = f'{self.api_uri}/me/'
        zoom_path = 'https://api.zoom.us/v2/users/me'
        zoom_users = self.get_zoom_api(zoom_path=zoom_path)
        return zoom_users
