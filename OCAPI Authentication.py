
# coding: utf-8

# # OCAPI Authentication

# In[1]:

import requests
import base64
import json
import os


# In[119]:

with open(os.path.expanduser("~/.dwre.json")) as f:
    SERVERS = json.load(f)
SERVER = SERVERS["projects"]["jss"]["environments"]["dev01"]
HOST = SERVER["server"]
PASSWORD = SERVER["password"]
CLIENT_ID = SERVER["apiClientId"]
API_CLIENT_PASSWORD = SERVER["apiClientPassword"]


# ## OAUTH Business Manager Grant

# Uses default `aaa..` client id used for sandboxes

# In[112]:


headers = {
    "authorization" : "Basic " + base64.b64encode("clavery:%s:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" % PASSWORD)
}

resp = requests.post('https://%s/dw/oauth2/access_token?client_id=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' % HOST, headers=headers, data={"grant_type" : "urn:demandware:params:oauth:grant-type:client-id:dwsid:dwsecuretoken"})
ACCESS_TOKEN = resp.json()["access_token"]


# In[113]:

get_ipython().magic(u'resp resp')


# In[110]:

headers = {
    "authorization" : "Bearer " + ACCESS_TOKEN
}
resp = requests.get("https://%s/s/-/dw/data/v17_1/catalogs?client_id=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb&count=100" % (HOST), headers=headers)


# In[111]:

get_ipython().magic(u'resp resp')


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

# In[120]:

#AUTH = (CLIENT_ID, API_CLIENT_PASSWORD)
AUTH = ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

resp = requests.post('https://account.demandware.com/dw/oauth2/access_token', auth=AUTH, data={"grant_type" : "client_credentials"})
ACCESS_TOKEN = resp.json()["access_token"]


# In[121]:

get_ipython().magic(u'resp resp')


# In[122]:

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
get_ipython().magic(u'resp resp')


# In[86]:

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
get_ipython().magic(u'resp resp')


# In[ ]:



