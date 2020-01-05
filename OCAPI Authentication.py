
# coding: utf-8

# # OCAPI Authentication



import requests
import base64
import json
import os





SERVER = "demo-na01-redwing.demandware.net"
HOST = "demo-na01-redwing.demandware.net"
CLIENT_ID = "..."
API_CLIENT_PASSWORD = "..."


# ## Client Credentials Grant

# ```
# REQUEST:
# POST /dw/oauth2/access_token HTTP/1.1
# Host: account.demandware.com
# Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==
# Content-Type: application/x-www-form-urlencoded
# 
# grant_type=client_credentials
# ```



AUTH = (CLIENT_ID, API_CLIENT_PASSWORD)

resp = requests.post('https://account.demandware.com/dw/oauth2/access_token', auth=AUTH, data={"grant_type" : "client_credentials"})
ACCESS_TOKEN = resp.json()["access_token"]




get_ipython().run_line_magic('resp', 'resp')




headers = {
    "authorization" : "Bearer " + ACCESS_TOKEN
}

params = {
    "expand" : "all"
}
resp = requests.get("https://%s/s/-/dw/data/v18_6/products/83923" % HOST, headers=headers, params=params)
get_ipython().run_line_magic('resp', 'resp')

