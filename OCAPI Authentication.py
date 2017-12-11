
# coding: utf-8

# # OCAPI Authentication



import requests
import base64
import json
import os




with open(os.path.expanduser("~/.dwre.json")) as f:
    SERVERS = json.load(f)
SERVER = SERVERS["projects"]["lbh"]["environments"]["dev01"]
HOST = SERVER["server"]
PASSWORD = SERVER["password"]
CLIENT_ID = SERVER["apiClientId"]
API_CLIENT_PASSWORD = SERVER["apiClientPassword"]


# ## OAUTH Business Manager Grant

# Uses default `aaa..` client id used for sandboxes




headers = {
    "authorization" : "Basic " + base64.b64encode(("clavery:%s:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" % PASSWORD).encode("utf-8")).decode("utf-8")
}

resp = requests.post('https://%s/dw/oauth2/access_token?client_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' % HOST, headers=headers, data={"grant_type" : "urn:demandware:params:oauth:grant-type:client-id:dwsid:dwsecuretoken"})
ACCESS_TOKEN = resp.json()["access_token"]




get_ipython().run_line_magic('resp', 'resp')




headers = {
    "authorization" : "Bearer " + ACCESS_TOKEN
}
j = {
    "file_name" : "test.zip"
}
resp = requests.post("https://%s/s/-/dw/data/v17_1/jobs/sfcc-save-instance-state/executions?client_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa&count=100" % (HOST), 
                     headers=headers, json=j)




get_ipython().run_line_magic('resp', 'resp')


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



#AUTH = (CLIENT_ID, API_CLIENT_PASSWORD)
AUTH = ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

resp = requests.post('https://account.demandware.com/dw/oauth2/access_token', auth=AUTH, data={"grant_type" : "client_credentials"})
ACCESS_TOKEN = resp.json()["access_token"]




get_ipython().run_line_magic('resp', 'resp')




headers = {
    "authorization" : "Bearer " + ACCESS_TOKEN
}

data = { 
  "query" : 
  {
"match_all_query": {}
    },
  "sorts":[{"field":"start_time", "sort_order":"asc"}]
}
resp = requests.post("https://%s/s/-/dw/data/v17_1/job_execution_search" % HOST, json=data, headers=headers)
get_ipython().run_line_magic('resp', 'resp')




headers = {
    "authorization" : "Bearer " + ACCESS_TOKEN
}

data = { 
  "query" : 
  {
"match_all_query": {}
    },
  "sorts":[{"field":"start_time", "sort_order":"asc"}]
}
resp = requests.get("https://%s/s/-/dw/data/v17_1/jobs/ExportOrders/executions/160002" % HOST, headers=headers)
get_ipython().run_line_magic('resp', 'resp')

