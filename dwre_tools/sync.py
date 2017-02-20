from __future__ import print_function

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

from colorama import Fore, Back, Style
from .bmtools import login_business_manager, activate_code_version

def cartridges_to_zip(cartridges, filename):
    zip_file_io = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_file_io, "w", zipfile.ZIP_DEFLATED)

    for (cart_location, cart_name) in cartridges:
        fcount = 0
        print("Collecting {0}{1}{2}".format(Fore.CYAN, cart_name, Fore.RESET), end='')
        for (dirpath, dirnames, filenames) in os.walk(cart_location):
            basepath = dirpath[len(cart_location)+1:]
            for fname in filenames:
                fcount = fcount + 1
                zip_file.write(os.path.join(dirpath, fname), os.path.join(filename, cart_name, basepath, fname))
        print("...{0} files".format(fcount))
    zip_file.close()
    return zip_file_io

def collect_cartridges(directory, cartridges=None):
    if cartridges is None:
        cartridges = []

    for root, dirs, files in os.walk(directory):
        if ".project" in files:
            cartridges.append( (root, os.path.basename(root)) )
    return cartridges


def sync_command(env, delete_code_version, cartridge_location="."):
    cartridges = collect_cartridges(cartridge_location)

    webdavsession = requests.session()
    webdavsession.verify = env["verify"]
    webdavsession.auth=(env["username"], env["password"],)
    webdavsession.cert = env["cert"]

    code_version = env["codeVersion"]

    zip_file = cartridges_to_zip(cartridges, code_version)

    if delete_code_version:
        print("Deleting code version...")
        response = webdavsession.delete("https://{0}/on/demandware.servlet/webdav/Sites/Cartridges/{1}".format(env["server"], code_version))

    print("Syncing code version {0}{1}{2} on {0}{3}{2}".format(Fore.YELLOW, code_version, Fore.RESET, env["server"]))
    dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/Cartridges/{1}.zip"
                .format(env["server"], code_version))
    response = webdavsession.put(dest_url, data=zip_file)
    response.raise_for_status()

    print("Extracting...")
    data = {"method" : "UNZIP"}
    response = webdavsession.post(dest_url, data=data)
    response.raise_for_status()

    response = webdavsession.delete(dest_url)
    response.raise_for_status()

    print("{0}Successfully synced cartridges with {1}{2}".format(Fore.GREEN, env["server"], Fore.RESET))

    if delete_code_version:
        print("Reactivating code version...")
        bmsession = requests.session()
        bmsession.verify = env["verify"]
        bmsession.cert = env["cert"]

        login_business_manager(env, bmsession)
        activate_code_version(env, bmsession, code_version)
        print("Done")
