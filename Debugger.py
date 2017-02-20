
# coding: utf-8

# In[115]:

get_ipython().magic(u'load_ext autoreload')


# In[116]:

get_ipython().magic(u'autoreload 2')


# In[117]:

import requests
from dwre_tools.env import get_default_environment, get_default_project
from dwre_tools.sync import collect_cartridges, sync_command


# In[118]:

CARTRIDGES = collect_cartridges("./test_cartridges/")
CARTRIDGES


# In[119]:

CLIENT_ID = "dwre-tools"
name, PROJECT = get_default_project()
name, ENV = get_default_environment(PROJECT)


# In[120]:

AUTH = ENV['username'], ENV['password']
HEADERS = {
    "x-dw-client-id" : CLIENT_ID
}


# In[138]:

ENV["verify"] = True
ENV["cert"] = None
sync_command(ENV, False, cartridge_location="test_cartridges/")


# In[122]:

BASE_URL = "https://{0}/s/-/dw/debugger/v1_0".format(ENV['server'])


# In[123]:

session = requests.session()
session.auth = AUTH
session.headers = HEADERS


# In[124]:

resp = session.delete(BASE_URL + "/client")


# In[125]:

resp = session.post(BASE_URL + "/client")


# In[126]:

resp = session.get(BASE_URL + "/breakpoints")
get_ipython().magic(u'resp resp')


# In[127]:

BREAKPOINTS = {
    "breakpoints" : [
        {
          "line_number":32,
          "script_path":"/app_debugtest/cartridge/controllers/DebuggerTesting.js"
        }
    ]
}


# In[128]:

resp = session.delete(BASE_URL + "/breakpoints")

resp = session.post(BASE_URL + "/breakpoints", json=BREAKPOINTS)
get_ipython().magic(u'resp resp')


# In[130]:

resp = session.get(BASE_URL + "/threads")

threads = resp.json().get("script_threads")
if threads:
    thread_id = threads[0].get("id")

get_ipython().magic(u'resp resp')


# In[109]:

resp = session.post(BASE_URL + "/threads/reset")
resp.status_code


# In[131]:

resp = session.get(BASE_URL + "/threads/%s/frames/0/members" % thread_id)
get_ipython().magic(u'resp resp')


# In[136]:

resp = session.post(BASE_URL + "/threads/%s/resume" % thread_id)
resp.status_code


# In[113]:

resp = session.get(BASE_URL + "/threads/%s/frames/0/eval" % thread_id, params={"expr" : "myMap.size()"})
get_ipython().magic(u'resp resp')


# In[135]:

resp = session.get(BASE_URL + "/threads/%s/frames/0/members" % thread_id, params={"object_path" : "myMap"})
get_ipython().magic(u'resp resp')


# In[ ]:



