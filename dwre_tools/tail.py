import requests
import time
import re
import sys
from xml.etree import ElementTree as ET

from colorama import Fore, Back, Style

from .webdav import get_directories, get_files

def compare_file_times(f1, f2):
    if f1 > f2:
        return 1
    elif f2 > f1:
        return -1
    return 0


def latest_logs(server, username, password, filters):
    response = requests.request('PROPFIND', 'https://' + server + '/on/demandware.servlet/webdav/Sites/Logs/',
                                auth=(username, password))
    x = ET.fromstring(response.content)
    log_files = get_files(x)
    latest_files = []
    for f in filters:
        files = sorted([l for l in log_files if l[0].startswith(f)], cmp=compare_file_times)
        if files:
            latest_files.append(files.pop())
    return latest_files


LOGLINE_RE = re.compile(r'^(\[\d{4}.+?\w{3}\])')
ERROR_RE = re.compile(r'(ERROR)')
def format_log_part(logpart):
    lines = logpart.splitlines()
    lines = [LOGLINE_RE.sub(Fore.BLUE + '\\1' + Fore.RESET, line) for line in lines]
    lines = [ERROR_RE.sub(Fore.RED + '\\1' + Fore.RESET, line) for line in lines]
    return '\n'.join(lines)


def tail_logs(server, username, password, filters, interval):
    log_files = latest_logs(server, username, password, filters)
    urls = ['https://' + server + '/on/demandware.servlet/webdav/Sites/Logs/' + log[0] for
            log in log_files]
    initial = [requests.head(url, auth=(username, password)) for url in urls]
    lengths = [i.headers.get("Content-Length") for i in initial]
    lengths = [0 if not l else int(l) for l in lengths]

    try:
        while True:
            time.sleep(interval)

            for i, log in enumerate(log_files):
                url ='https://' + server + '/on/demandware.servlet/webdav/Sites/Logs/' + log[0]
                check = requests.head(url, auth=(username, password))
                content_length = check.headers.get("Content-Length")
                newlength = int(content_length) if content_length else 0
                if newlength > lengths[i]:
                    response = requests.get(url, auth=(username, password), headers={
                        "range" : "bytes=%s-%s" % (lengths[i], newlength-1)
                    })
                    print
                    print(Fore.GREEN + ("------ %s " % log[0]) + Fore.RESET)
                    print(Fore.GREEN + "------------------------------------------------" + Fore.RESET)
                    print format_log_part(response.content)
                    print(Fore.GREEN + "------------------------------------------------" + Fore.RESET)
                    print
                lengths[i] = newlength
    except KeyboardInterrupt, e:
        sys.exit(0)

