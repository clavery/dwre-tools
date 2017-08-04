
# coding: utf-8

# # Initial Steps

# - `mkdir -p ./DWREApiDoc.docset/Contents/Resources/Documents`
# - copy scriptapi/api to Documents/api and pipeletapi/api to Documents/pipelet (i.e. rename folder to pipelet)
# - Run this script



from pyquery import PyQuery as pq
import sqlite3
import os.path
import shutil
import markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from jinja2 import Template




PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>CFBundleIdentifier</key>
<string>oms</string>
<key>CFBundleName</key>
<string>OMS</string>
<key>DocSetPlatformFamily</key>
<string>oms</string>
<key>isDashDocset</key>
<true/>
</dict>
</plist>"""


# # Init



if not os.path.exists('./OrderManagement.docset/Contents/Resources/Documents/'):
    os.makedirs('./OrderManagement.docset/Contents/Resources/Documents/')
    
shutil.rmtree("./OrderManagement.docset/Contents/")

if not os.path.exists('./OrderManagement.docset/Contents/Resources/Documents/'):
    os.makedirs('./OrderManagement.docset/Contents/Resources/Documents/')

shutil.copy('./dwredocs/code.css', './OrderManagement.docset/Contents/Resources/Documents/code.css')

with open('./OrderManagement.docset/Contents/Info.plist', 'w') as f:
    f.write(PLIST)
    
conn = sqlite3.connect('./OrderManagement.docset/Contents/Resources/docSet.dsidx')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);")
c.execute("CREATE UNIQUE INDEX IF NOT EXISTS anchor ON searchIndex (name, type, path);")
conn.commit()


# # Script API



if os.path.exists("./OrderManagement.docset/Contents/Resources/Documents/api"):
    shutil.rmtree("./OrderManagement.docset/Contents/Resources/Documents/api")
shutil.copytree("./oms/documentation.demandware.com/API1/topic/com.demandware.dochelp/DWAPP-17.7-API-doc/scriptapi/html/api/", "./OrderManagement.docset/Contents/Resources/Documents/api")




with open("./OrderManagement.docset/Contents/Resources/Documents/api/classList.html", "r") as f:
    d = pq(f.read())

c = conn.cursor()

for link in d('table a'):

    title = link.attrib["title"]
    name = link.text
    path = link.attrib["href"]
    if "dw.om" not in title:
        continue
    print(name, title, path)
    
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Class', '%s');" % 
              (name, "api/%s" % path))
    
conn.commit()
def test():
    pass




conn.close()











