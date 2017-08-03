
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


# # Sample/Guides



with open('./dwredocs/guidetemplate.html', 'r') as f:
    template_src = f.read()
template = Template(template_src)

if not os.path.exists('./DWREApiDoc.docset/Contents/Resources/Documents/guides/'):
    os.makedirs('./DWREApiDoc.docset/Contents/Resources/Documents/guides/')
    
for f in os.listdir('./dwredocs/guides/'):
    name, ext = os.path.splitext(f)
    print name
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
    print name
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
    print name
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




conn.close()






