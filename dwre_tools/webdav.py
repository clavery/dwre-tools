from __future__ import print_function

from xml.etree import ElementTree as ET
from datetime import datetime
import pytz

import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

# File node reference
# <ns0:response xmlns:ns0="DAV:"><ns0:href>/on/demandware.servlet/webdav/Sites/Logs/warn-blade1-4.mon.demandware.net-appserver-20170723.log</ns0:href>
# <ns0:propstat><ns0:prop><ns0:creationdate>2017-07-23T23:59:01Z</ns0:creationdate>
# <ns0:getlastmodified>Sun, 23 Jul 2017 23:59:01 GMT</ns0:getlastmodified>
# <ns0:displayname>warn-blade1-4.mon.demandware.net-appserver-20170723.log</ns0:displayname>
# <ns0:getcontentlength>44248</ns0:getcontentlength>
# <ns0:getcontenttype>text/plain</ns0:getcontenttype>
# <ns0:getetag>6aa28f582d76b474c22787937016b8f6</ns0:getetag>
# <ns0:resourcetype /></ns0:prop>
# <ns0:status>HTTP/1.1 200 OK</ns0:status>
# </ns0:propstat>
# </ns0:response>

def get_directories(tree, root):
    names = tree.findall(".//{DAV:}collection/../../{DAV:}displayname")
    return sorted([n.text for n in names if root != n.text])


def file_convert_date(filetup):
    tup = (filetup[0], datetime.strptime(filetup[1], "%a, %d %b %Y %H:%M:%S GMT"))
    tup = (tup[0], tup[1].replace(tzinfo=pytz.utc))
    return tup

def get_files(tree):
    filenodes = [n for n in tree.iterfind("./") if not n.findall(".//{DAV:}collection")]
    filetuples = [(n.find('.//{DAV:}displayname').text, n.find('.//{DAV:}getlastmodified').text)
                  for n in filenodes if n.find('.//{DAV:}displayname').text != 'soa']
    return [file_convert_date(t) for t in filetuples]


def list_dir(location, username, password):
    response = requests.request('PROPFIND', location, auth=(username, password), headers=HEADERS)
    response.raise_for_status()
    x = ET.fromstring(response.content)
    return ( get_directories(x, ''), get_files(x) )


def copy_command(env, src, dest):
    webdavsession = requests.session()
    webdavsession.verify = env["verify"]
    webdavsession.auth=(env["username"], env["password"],)
    webdavsession.cert = env["cert"]

    if dest[0] == '/':
        dest = dest[1:]

    dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/{1}"
                .format(env["server"], dest))

    with open(src, "rb") as f:
        response = webdavsession.put(dest_url, data=f)
        response.raise_for_status()

    print("Copied {0} to {1}".format(src, dest_url))
