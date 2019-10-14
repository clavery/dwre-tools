#!/usr/bin/env python
# coding: utf-8

# # Initial Steps

# - get api from https://dev04-na01-XXX.demandware.net:443/on/demandware.servlet/WFS/Studio/Sites/mock/demandware-mock.zip
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
import requests




PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>CFBundleIdentifier</key>
<string>dwre</string>
<key>CFBundleName</key>
<string>DWRE</string>
<key>DocSetPlatformFamily</key>
<string>dwre</string>
<key>isDashDocset</key>
<true/>
</dict>
</plist>"""


# # Init



if os.path.exists("./DWREApiDoc.docset/Contents/"):
    shutil.rmtree("./DWREApiDoc.docset/Contents/")

if not os.path.exists('./DWREApiDoc.docset/Contents/Resources/Documents/'):
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/')

shutil.copy('./dwredocs/code.css', './DWREApiDoc.docset/Contents/Resources/Documents/code.css')

with open('./DWREApiDoc.docset/Contents/Info.plist', 'w') as f:
    f.write(PLIST)
    
conn = sqlite3.connect('./DWREApiDoc.docset/Contents/Resources/docSet.dsidx')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);")
c.execute("CREATE UNIQUE INDEX IF NOT EXISTS anchor ON searchIndex (name, type, path);")
conn.commit()


# # Script API



if os.path.exists("./DWREApiDoc.docset/Contents/Resources/Documents/api"):
    shutil.rmtree("./DWREApiDoc.docset/Contents/Resources/Documents/api")
shutil.copytree("./dwredocs/scriptapi/html/api", "./DWREApiDoc.docset/Contents/Resources/Documents/api")




with open("./DWREApiDoc.docset/Contents/Resources/Documents/api/classList.html", "r") as f:
    d = pq(f.read())
    
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


# ## Job Step API



if os.path.exists("./DWREApiDoc.docset/Contents/Resources/Documents/jobstepapi/"):
    shutil.rmtree("./DWREApiDoc.docset/Contents/Resources/Documents/jobstepapi/")
shutil.copytree("./dwredocs/jobstepapi/html/api/", "./DWREApiDoc.docset/Contents/Resources/Documents/jobstepapi")




with open("./DWREApiDoc.docset/Contents/Resources/Documents/jobstepapi/jobStepList.html", "r") as f:
    d = pq(f.read())

c = conn.cursor()

for link in d('.classesName a'):
    name = link.find("span").text
    path = link.attrib["href"]
    
    print(name, path)
    
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Builtin', '%s');" % 
              (name, "jobstepapi/%s" % path))
    
conn.commit()


# # Pipelet API



if os.path.exists("./DWREApiDoc.docset/Contents/Resources/Documents/pipelet/"):
    shutil.rmtree("./DWREApiDoc.docset/Contents/Resources/Documents/pipelet/")
shutil.copytree("./dwredocs/pipeletapi/html/api/", "./DWREApiDoc.docset/Contents/Resources/Documents/pipelet")




with open("./DWREApiDoc.docset/Contents/Resources/Documents/pipelet/pipeletList.html", "r") as f:
    d = pq(f.read())

c = conn.cursor()

for link in d('.classesName a'):
    name = link.find("span").text
    path = link.attrib["href"]
    
    print(name, path)
    
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Procedure', '%s');" % 
              (name, "pipelet/%s" % path))
    
conn.commit()


# # Pipelet API



if os.path.exists("./DWREApiDoc.docset/Contents/Resources/Documents/pipelet/"):
    shutil.rmtree("./DWREApiDoc.docset/Contents/Resources/Documents/pipelet/")
shutil.copytree("./dwredocs/pipeletapi/html/api/", "./DWREApiDoc.docset/Contents/Resources/Documents/pipelet")


# # Sample/Guides



with open('./dwredocs/guidetemplate.html', 'r') as f:
    template_src = f.read()
template = Template(template_src)

if not os.path.exists('./DWREApiDoc.docset/Contents/Resources/Documents/guides/'):
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/guides/')
    
for f in os.listdir('./dwredocs/guides/'):
    name, ext = os.path.splitext(f)
    print(name)
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Guide', '%s');" % 
              (name, "guides/%s" % (name+".html")))
    
    with open('./dwredocs/guides/' + f, 'r') as f:
        doc_output = markdown.markdown(f.read(), extensions=[TableExtension(), FencedCodeExtension(), CodeHiliteExtension()])

    with open(os.path.join('./DWREApiDoc.docset/Contents/Resources/Documents/guides/', name+".html"), 'w') as f:
        output = template.render(body=doc_output)
        f.write(output)

conn.commit()


# # ISML Tags



if not os.path.exists('./DWREApiDoc.docset/Contents/Resources/Documents/isml/'):
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/isml/')
    
for f in os.listdir('./dwredocs/isml/'):
    name, ext = os.path.splitext(f)
    print(name)
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Tag', '%s');" % 
              (name, "isml/%s" % (name+".html")))
    
    shutil.copy('./dwredocs/isml/' + f, './DWREApiDoc.docset/Contents/Resources/Documents/isml/' + f)

conn.commit()


# # Schemas



with open('./dwredocs/schematemplate.html', 'r') as f:
    template_src = f.read()
template = Template(template_src)

if not os.path.exists('./DWREApiDoc.docset/Contents/Resources/Documents/schemas/'):
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/schemas/')
for f in os.listdir('./dwredocs/xsd/'):
    name, ext = os.path.splitext(f)
    if ext != ".xsd":
        continue
    print(name)
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', 'Protocol', '%s');" % 
              (f, "schemas/%s" % (name+".html")))
    
    with open('./dwredocs/xsd/' + f, 'r') as f:
        md = """
```xml
%s
```
        """ % f.read()
        doc_output = markdown.markdown(md, extensions=[TableExtension(), FencedCodeExtension(), CodeHiliteExtension()])

    with open(os.path.join('./DWREApiDoc.docset/Contents/Resources/Documents/schemas/', name+".html"), 'w') as f:
        output = template.render(body=doc_output, name=name)
        f.write(output)

conn.commit()







# ## OCAPI

# Place the cookies from chrome (in normal cookie header format) in .cookies



V = "current"
OCAPI_PREFIX = '/DOC3/topic/com.demandware.dochelp/OCAPI/%s/' % V
OCAPI_INDICIES = [
    'https://documentation.b2c.commercecloud.salesforce.com/DOC3/topic/com.demandware.dochelp/OCAPI/%s/shop/Resources/index.html' % V,
    'https://documentation.b2c.commercecloud.salesforce.com/DOC3/topic/com.demandware.dochelp/OCAPI/%s/data/Resources/index.html' % V,
    'https://documentation.b2c.commercecloud.salesforce.com/DOC3/topic/com.demandware.dochelp/OCAPI/%s/usage/APIUsage.html?cp=0_12_2' % V,
    'https://documentation.b2c.commercecloud.salesforce.com/DOC3/topic/com.demandware.dochelp/OCAPI/%s/shop/Documents/index.html' % V,
    'https://documentation.b2c.commercecloud.salesforce.com/DOC3/topic/com.demandware.dochelp/OCAPI/%s/data/Documents/index.html' % V
]




from lxml import etree as ET
from io import StringIO




NS = "{http://www.w3.org/1999/xhtml}"
NSMAP = {
    "X" : "http://www.w3.org/1999/xhtml"
}
from urllib.parse import urlparse
LINKS = set()
for page in OCAPI_INDICIES:
    r = requests.get(page)
    content = r.content.decode('utf-8').replace('self == top', 'self == "blah"').encode('utf-8')
    parser = ET.HTMLParser()
    content = ET.fromstring(content, parser)
    parsed_url = urlparse(page)
    dirname = os.path.normpath(os.path.dirname(parsed_url.path))
    if OCAPI_PREFIX not in dirname:
        continue

    for link in content.xpath("//a", namespaces=NSMAP):
        href = link.attrib['href']
        normalized = os.path.normpath(os.path.join(dirname, href))
        full_link = urlparse(f"{parsed_url.scheme}://{parsed_url.netloc}{normalized}")
        full_link = f"{full_link.scheme}://{full_link.netloc}{full_link.path}"
        if OCAPI_PREFIX not in full_link:
            continue
        print(full_link)
        if full_link.endswith('.html'):
            LINKS.add(full_link)
            
resp = requests.get('https://documentation.demandware.com/DOC3/topic/com.demandware.dochelp/css/commonltr.css')
css = f"""<style>
{resp.content.decode('utf-8')}
</style>"""




page




if os.path.exists("./DWREApiDoc.docset/Contents/Resources/Documents/ocapi"):
    shutil.rmtree("./DWREApiDoc.docset/Contents/Resources/Documents/ocapi")
    
if not os.path.exists('./DWREApiDoc.docset/Contents/Resources/Documents/ocapi/'):
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/ocapi/shop/Documents')
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/ocapi/data/Documents')
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/ocapi/shop/Resources')
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/ocapi/data/Resources')




for link in LINKS:
    r = requests.get(link)
    r.raise_for_status()
    content = r.content.decode('utf-8').replace('self == top', 'self == "blah"')
    content = content.replace("</head>", css)
    name, ext = os.path.splitext(os.path.basename(link))
    print(name)
    if "shop/Resources" in link:
        entry_type = "Resource"
        entry_name = "SHOPAPI " + name
        entry_folder = "shop/Resources/"
    elif "shop/Documents" in link:
        entry_type = "Type"
        entry_name = "SHOPDOC "  + name
        entry_folder = "shop/Documents/"
    elif "data/Resources" in link:
        entry_type = "Resource"
        entry_name = "DATAAPI " + name
        entry_folder = "data/Resources/"
    elif "data/Documents" in link:
        entry_type = "Type"
        entry_name = "DATADOC "  + name
        entry_folder = "data/Documents/"
    else:
        entry_type = "Guide"
        entry_name = name
        entry_folder = ""
        
    c.execute("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('%s', '%s', '%s');" % 
              (entry_name, entry_type, "ocapi/%s%s" % (entry_folder, name+".html")))
    with open(os.path.join('./DWREApiDoc.docset/Contents/Resources/Documents/ocapi/%s' % entry_folder, name+".html"), 'w') as f:
        f.write(content)
conn.commit()




conn.close()











