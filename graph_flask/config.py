"""Configuration settings for running the Python auth samples locally.

In a production deployment, this information should be saved in a database or
other secure storage mechanism.
"""
import os
from urllib import parse
from flask import request
zoom_client_id = os.environ.get("zoom_client_id")
zoom_client_secret = os.environ.get('zoom_client_secret')

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')



REDIRECT_PATH = "/getAToken"  # Used for forming an absolute URL to your redirect URI.
                              # The absolute URL must match the redirect URI you set
                              # in the app's registration in the Azure portal.
ENDPOINT = 'https://graph.microsoft.com/v1.0/users'  # This resource requires no admin consent
SCOPE = [
         "AccessReview.ReadWrite.Membership",
         "ChannelMessage.Read.All",
         "Directory.ReadWrite.All",
         "Files.ReadWrite.All",
         "Group.ReadWrite.All",
         "Sites.ReadWrite.All",
         "User.ReadWrite.All",
         "User.ReadBasic.All",
         ]



# AUTHORITY_URL ending determines type of account that can be authenticated:
# /organizations = organizational accounts only
# /consumers = MSAs only (Microsoft Accounts - Live.com, Hotmail.com, etc.)
# /common = allow both types of accounts
# AUTHORITY_URL = 'https://login.microsoftonline.com/smartpropertyportal'

AUTH_ENDPOINT = '/oauth2/v2.0/authorize'
TOKEN_ENDPOINT = '/oauth2/v2.0/token'
ALLOW_REDIRECT_PATH = ['https://smartsgportal.azurewebsites.net/',
# 'http://localhost:3000/',   
'https://smartpropertyportal.azurewebsites.net/']
    
RESOURCE = 'https://graph.microsoft.com/'
API_VERSION = 'v1.0'
connecting_string ="Driver={ODBC Driver 17 for SQL Server};Server=tcp:smartpropertysingapore.database.windows.net,1433;Database=smartpropertyadmin;Uid=smartpropertyadmin;Pwd=" +f"{os.environ.get('smartpropertyadmin_azure_db_pw')};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
params = parse.quote_plus(connecting_string)
# AUTHORITY = 'https://login.microsoftonline.com/common'
AUTHORITY = 'https://login.microsoftonline.com/001ef4ed-66e5-4e4e-a6d0-f5a6123827dc'  # For multi-tenant app
ISSUER="https://login.microsoftonline.com/001ef4ed-66e5-4e4e-a6d0-f5a6123827dc/v2.0"


class Config:
    # SESSION_TYPE = "filesystem"  # Specifies the token cache should be stored in server-side session
    SECRET_KEY = os.environ.get('secret_key')
    CORS_HEADERS = 'Content-Type'
    
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect=%s" % params
    SQLALCHEMY_BINDS = {
        'Main' : "mssql+pyodbc:///?odbc_connect=%s" % params,
    }

    MAIL_SERVER = "smtp.office365.com"
    MAIL_PORT = '587'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    # SESSION_TYPE = "filesystem"
# 
