from xml.etree import ElementTree as ET
import requests
from datetime import datetime


def get_directories(tree, root):
    names = tree.findall(".//{DAV:}collection/../../{DAV:}displayname")
    return sorted([n.text for n in names if root != n.text])


# Fri, 15 May 2015 15:37:14 GMT
def file_convert_date(filetup):
    return (filetup[0], datetime.strptime(filetup[1], "%a, %d %b %Y %H:%M:%S GMT"))

def get_files(tree):
    filenodes = [n for n in tree.iterfind("./") if not n.findall(".//{DAV:}collection")]
    filetuples = [(n.find('.//{DAV:}displayname').text, n.find('.//{DAV:}getlastmodified').text)
                  for n in filenodes if n.find('.//{DAV:}displayname').text != 'soa']
    return [file_convert_date(t) for t in filetuples]


def list_dir(location, username, password):
    response = requests.request('PROPFIND', location, auth=(username, password))
    x = ET.fromstring(response.content)
    return ( get_directories(x, ''), get_files(x) )

