import sys
import requests
import yaml
import re
import tempfile
import uuid
import zipfile, io
import shutil
import io
import zipfile
import os

from prompt_toolkit.shortcuts.progress_bar.formatters import Progress, create_default_formatters
from prompt_toolkit.formatted_text import HTML
import math
from prompt_toolkit.shortcuts import ProgressBar
from colorama import Fore, Back, Style
from .bmtools import login_business_manager, activate_code_version

def cartridges_to_zip(cartridges, filename):
    zip_file_io = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_file_io, "w", zipfile.ZIP_DEFLATED)

    _, real_filename = os.path.split(filename)
    for (cart_location, cart_name) in cartridges:
        fcount = 0
        print("Collecting {0}{1}{2}".format(Fore.CYAN, cart_name, Fore.RESET), end='')
        for (dirpath, dirnames, filenames) in os.walk(cart_location):
            basepath = dirpath[len(cart_location)+1:]
            for fname in filenames:
                fcount = fcount + 1
                zip_file.write(os.path.join(dirpath, fname), os.path.join(real_filename, cart_name, basepath, fname))
        print("...{0} files".format(fcount))
    zip_file.close()
    return zip_file_io

BAD_DIRS = ["node_modules", "tools"]
def collect_cartridges(directory, cartridges=None):
    if cartridges is None:
        cartridges = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in BAD_DIRS]
        if ".project" in files:
            cartridges.append( (root, os.path.basename(root)) )
    return cartridges


class StreamingIO():
    def __init__(self, file, chunk=1000):
        self.file = file
        self.file.seek(0)
        self.chunk = chunk

    def __iter__(self):
        while True:
            data = self.file.read(self.chunk)
            if not data:
                break
            yield data


class FileSizeProgress(Progress):
    template = '{current:.2f}/{total:.2f}KB'

    def __init__(self, chunk, total):
        super()
        self._chunk = chunk
        self._total = total

    def format(self, progress_bar, progress, width):
        current = min(progress.current * self._chunk / 1024, self._total / 1024)
        return self.template.format(
            current=current,
            total=self._total / 1024)

    def get_width(self, progress_bar):
        return 20


def sync_command(env, delete_code_version, cartridge_location):
    if cartridge_location is None:
        cartridge_location = '.'

    webdavsession = requests.session()
    webdavsession.verify = env["verify"]
    webdavsession.auth=(env["username"], env["password"],)
    webdavsession.cert = env["cert"]
    code_version = env["codeVersion"]

    if os.path.isfile(cartridge_location):
        # zip file instead of dir
        with tempfile.TemporaryDirectory() as tempdir:
            with zipfile.ZipFile(cartridge_location, 'r') as stored_zip:
                stored_zip.extractall(path=tempdir)
            cartridges = collect_cartridges(tempdir)
            zip_file = cartridges_to_zip(cartridges, code_version)
    else:
        cartridges = collect_cartridges(cartridge_location)
        zip_file = cartridges_to_zip(cartridges, code_version)

    if delete_code_version:
        print("Deleting code version...")
        response = webdavsession.delete("https://{0}/on/demandware.servlet/webdav/Sites/Cartridges/{1}".format(env["server"], code_version))
        response.raise_for_status()

    print("Syncing code version {0}{1}{2} on {0}{3}{2}".format(Fore.YELLOW, code_version, Fore.RESET, env["server"]))
    dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/Cartridges/{1}.zip"
                .format(env["server"], code_version))
    total = zip_file.getbuffer().nbytes
    progress_format = create_default_formatters()
    progress_format[6] = FileSizeProgress(4096, total)
    if sys.stdout.isatty() and sys.stdin.isatty():
        with ProgressBar(formatters=progress_format) as pb:
            response = webdavsession.put(dest_url,
                                         data=pb(StreamingIO(zip_file, chunk=4096),
                                                 total=math.ceil(total/4096)))
            response.raise_for_status()
    else:
        response = webdavsession.put(dest_url,
                                     data=StreamingIO(zip_file, chunk=4096))
        response.raise_for_status()

    print("Extracting...")
    data = {"method": "UNZIP"}
    response = webdavsession.post(dest_url, data=data)
    response.raise_for_status()

    response = webdavsession.delete(dest_url)
    response.raise_for_status()

    print(f"{Fore.GREEN}Successfully synced cartridges with {env['server']}{Fore.RESET}")

    if delete_code_version:
        print("Reactivating code version...")
        bmsession = requests.session()
        bmsession.verify = env["verify"]
        bmsession.cert = env["cert"]

        login_business_manager(env, bmsession)
        activate_code_version(env, bmsession, code_version)
        print("Done")
