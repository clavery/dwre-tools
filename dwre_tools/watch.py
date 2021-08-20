import os
import time
import io
import zipfile
import uuid
from threading import Timer

import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from colorama import Fore

from .sync import collect_cartridges
from .bmtools import authenticate_webdav_session


class SFCCWebdavUploaderEventHandler(FileSystemEventHandler):
    def __init__(self, env, path, name, zip_files=True):
        webdavsession = authenticate_webdav_session(env)

        self.env = env
        self.cartridge_name = name
        self.cartridge_path = path
        self.session = webdavsession
        self.zip_files = zip_files
        self.code_version = env["codeVersion"]
        self.server = env["server"]
        self.base_url = (f"https://{self.server}/on/demandware.servlet/webdav/Sites/" +
                         f"Cartridges/{self.code_version}")

        self.upload_queue = set()

    def upload(self, retry=False):
        # TODO: check for thread safety here
        queue = self.upload_queue.copy()
        self.upload_queue = set()
        if not queue:
            return

        zip_file_io = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_file_io, "w", zipfile.ZIP_DEFLATED)
        for file in queue:
            prefix = os.path.commonprefix([self.cartridge_path, file])
            suffix = file[len(prefix):]
            normpath = self.cartridge_name + suffix

            zip_file.write(file, normpath)

        zip_file.close()
        zip_file_io.seek(0)

        temp_name = str(uuid.uuid4()) + ".zip"
        dest_url = f"{self.base_url}/{temp_name}"
        response = self.session.put(dest_url, data=zip_file_io)
        if response.status_code == 401 and not retry:
            print("Re-Authenticating")
            self.session = authenticate_webdav_session(self.env)
            self.upload_queue = queue
            self.upload(retry=True)
        elif response.status_code == 403 and not retry:
            print("Re-Authenticating")
            self.session = authenticate_webdav_session(self.env)
            self.upload_queue = queue
            self.upload(retry=True)
        else:
            response.raise_for_status()
        data = {"method": "UNZIP"}
        response = self.session.post(dest_url, data=data)
        response.raise_for_status()
        response = self.session.delete(dest_url)
        response.raise_for_status()
        print(f"{Fore.GREEN}Uploaded{Fore.RESET}")
        for file in queue:
            prefix = os.path.commonprefix([self.cartridge_path, file])
            suffix = file[len(prefix):]
            normpath = self.cartridge_name + suffix
            print(f"\t{Fore.GREEN}- {normpath}{Fore.RESET}")

    def upload_file(self, file):
        prefix = os.path.commonprefix([self.cartridge_path, file])
        suffix = file[len(prefix):]
        normpath = self.cartridge_name + suffix
        temp_name = str(uuid.uuid4()) + ".zip"
        dest_url = f"{self.base_url}/{temp_name}"
        with open(file, 'rb') as f:
            response = self.session.put(dest_url, data=f)
            response.raise_for_status()
        print(f"{Fore.GREEN}Uploaded{Fore.RESET}")
        print(f"\t{Fore.GREEN}- {normpath}{Fore.RESET}")

    def on_created(self, event):
        print(f"[CREATED] {event.src_path}")
        if self.zip_files:
            self.upload_queue.add(event.src_path)
            t = Timer(0.200, self.upload)
            t.start()
        else:
            self.upload_file(event.src_path)

    def on_modified(self, event):
        print(f"[MODIFIED] {event.src_path}")
        if self.zip_files:
            self.upload_queue.add(event.src_path)
            t = Timer(0.200, self.upload)
            t.start()
        else:
            self.upload_file(event.src_path)


def watch_command(env, directory, zip_files=True):
    if directory is None:
        directory = '.'

    cartridges = collect_cartridges(directory)

    print(f"{Fore.GREEN}Watching {directory}; Uploading to {env['server']} " +
          f"code version {env['codeVersion']}{Fore.RESET}")

    observer = Observer()
    for cartridge_path, cartridge_name in cartridges:
        print(f"Watching {cartridge_name}")
        webdav_event_handler = SFCCWebdavUploaderEventHandler(env, cartridge_path, cartridge_name, zip_files=zip_files)
        observer.schedule(webdav_event_handler, cartridge_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
