
# coding: utf-8

# # OCAPI Authentication

# In[1]:

import requests
import base64
import json
import os


# In[59]:

with open(os.path.expanduser("~/.dwre.json")) as f:
    SERVERS = json.load(f)
DEV01 = SERVERS["projects"]["ktp"]["environments"]["dev01"]
PASSWORD = DEV01["password"]
CLIENT_ID = DEV01["apiClientId"]
API_CLIENT_PASSWORD = DEV01["apiClientPassword"]


# In[56]:

PASSWORD


# ## OAUTH Business Manager Grant

# Uses default `aaa..` client id used for sandboxes

# In[2]:


headers = {
    "authorization" : "Basic " + base64.b64encode("clavery:%s:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" % PASSWORD)
}

resp = requests.post('https://dev01-web-ktp.demandware.net/dw/oauth2/access_token?client_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', headers=headers, data={"grant_type" : "urn:demandware:params:oauth:grant-type:client-id:dwsid:dwsecuretoken"})
ACCESS_TOKEN = resp.json()["access_token"]


# In[3]:

get_ipython().magic(u'resp resp')


# In[6]:

headers = {
    "authorization" : "Bearer " + ACCESS_TOKEN
}
resp = requests.get("https://dev01-web-ktp.demandware.net/s/-/dw/data/v17_1/system_object_definitions?client_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa&count=100", headers=headers)


# In[8]:

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

# In[60]:

AUTH = (CLIENT_ID, API_CLIENT_PASSWORD)


resp = requests.post('https://account.demandware.com/dw/oauth2/access_token', auth=AUTH, data={"grant_type" : "client_credentials"})
ACCESS_TOKEN = resp.json()["access_token"]


# In[61]:

get_ipython().magic(u'resp resp')


# In[62]:

headers = {
    "authorization" : "Bearer " + ACCESS_TOKEN
}
resp = requests.get("https://dev01-web-ktp.demandware.net/s/-/dw/data/v17_1/system_object_definitions?count=100", headers=headers)
get_ipython().magic(u'resp resp')


# In[ ]:



