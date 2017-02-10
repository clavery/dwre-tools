
# coding: utf-8

# # Initial Steps

# - `mkdir -p ./DWREApiDoc.docset/Contents/Resources/Documents`
# - copy scriptapi/api to Documents/api and pipeletapi/api to Documents/pipelet (i.e. rename folder to pipelet)
# - Run this script

# In[2]:

from pyquery import PyQuery as pq
import sqlite3
conn = sqlite3.connect('./DWREApiDoc.docset/Contents/Resources/docSet.dsidx')


# # Init

# In[3]:

c = conn.cursor()
c.execute("CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);")
c.execute("CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);")
conn.commit()


# # Script API

# In[4]:

with open("./DWREApiDoc.docset/Contents/Resources/Documents/api/classList.html", "r") as f:
    d = pq(f.read())


# In[5]:

c = conn.cursor()

for link in d('.classesName a'):
    title = link.attrib["title"]
    name = link.text
    path = link.attrib["href"]
    
    print(name, title, path)
    
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Class', '%s');" % 
              (name, "api/%s" % path))
    
conn.commit()
def test():
    pass


# # Pipelet API

# In[6]:

with open("./DWREApiDoc.docset/Contents/Resources/Documents/pipelet/pipeletList.html", "r") as f:
    d = pq(f.read())


# In[7]:

c = conn.cursor()

for link in d('.classesName a'):
    name = link.find("span").text
    path = link.attrib["href"]
    
    print(name, path)
    
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Procedure', '%s');" % 
              (name, "pipelet/%s" % path))
    
conn.commit()
conn.close()


# In[8]:

conn.close()


# In[9]:

get_ipython().run_cell_magic(u'javascript', u'', u'\nconsole.log("tesT");')


# In[ ]:




# In[ ]:




# In[ ]:



