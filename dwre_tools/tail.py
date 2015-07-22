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
    response.raise_for_status()
    x = ET.fromstring(response.content)
    log_files = get_files(x)
    latest_files = []
    for f in filters:
        files = sorted([l for l in log_files if l[0].startswith(f)], cmp=compare_file_times)
        if files:
            latest_files.append(files.pop())
    return latest_files


LOGLINE_RE = re.compile(r'^(\[\d{4}.+?\w{3}\])')
LOGENTRY_RE = re.compile(r'^(?:\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \w{3}\]).*?(?=(?:\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \w{3}\])|\Z)', re.S|re.M)
ERROR_RE = re.compile(r'(ERROR)')
def format_log_part(logpart):
    lines = logpart.splitlines()
    lines = [LOGLINE_RE.sub(Fore.BLUE + '\\1' + Fore.RESET, line) for line in lines]
    lines = [ERROR_RE.sub(Fore.RED + '\\1' + Fore.RESET, line) for line in lines]
    return '\n'.join(lines)


def output_log_file(name, content):
    print
    print(Fore.GREEN + ("------ %s " % name) + Fore.RESET)
    print(Fore.GREEN + "------------------------------------------------" + Fore.RESET)
    print format_log_part(content)
    print(Fore.GREEN + "------------------------------------------------" + Fore.RESET)
    print


def tail_log_file(name, content):
    error_lines = LOGENTRY_RE.findall(content)
    if error_lines:
        output_log_file(name, error_lines[-1])


def tail_logs(env, filters, interval):
    # TODO allow usage with client cert, noverify
    server = env["server"]
    username = env["username"]
    password = env["password"]

    log_files = latest_logs(server, username, password, filters)
    urls = ['https://' + server + '/on/demandware.servlet/webdav/Sites/Logs/' + log[0] for
            log in log_files]

    initial = [requests.head(url, auth=(username, password)) for url in urls]
    [r.raise_for_status() for r in initial]

    lengths = [i.headers.get("Content-Length") for i in initial]
    lengths = [0 if not l else int(l) for l in lengths]

    # get initial for last line purposes (for some reason this returns diff content lengths so we
    # can't use it for the initial length calc
    tail_requests = [requests.get(url, auth=(username, password)) for url in urls]
    [tail_log_file(log[0], r.content) for r, log in zip(tail_requests, log_files)]

    try:
        while True:
            time.sleep(interval)

            for i, log in enumerate(log_files):
                url ='https://' + server + '/on/demandware.servlet/webdav/Sites/Logs/' + log[0]
                check = requests.head(url, auth=(username, password))
                check.raise_for_status()

                content_length = check.headers.get("Content-Length")
                newlength = int(content_length) if content_length else 0
                if newlength > lengths[i]:
                    response = requests.get(url, auth=(username, password), headers={
                        "range" : "bytes=%s-%s" % (lengths[i], newlength-1)
                    })
                    response.raise_for_status()
                    output_log_file(log[0], response.content)
                lengths[i] = newlength
    except KeyboardInterrupt, e:
        sys.exit(0)

