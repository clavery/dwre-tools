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


class SFCCWebdavUploaderEventHandler(FileSystemEventHandler):
    def __init__(self, env, path, name):
        webdavsession = requests.session()
        webdavsession.verify = env["verify"]
        webdavsession.auth = (env["username"], env["password"], )
        webdavsession.cert = env["cert"]

        self.cartridge_name = name
        self.cartridge_path = path
        self.session = webdavsession
        self.code_version = env["codeVersion"]
        self.server = env["server"]
        self.base_url = (f"https://{self.server}/on/demandware.servlet/webdav/Sites/" +
                         f"Cartridges/{self.code_version}")

        self.upload_queue = set()

    def upload(self):
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

    def on_created(self, event):
        print(f"[CREATED] {event.src_path}")
        self.upload_queue.add(event.src_path)
        t = Timer(0.200, self.upload)
        t.start()

    def on_modified(self, event):
        print(f"[MODIFIED] {event.src_path}")
        self.upload_queue.add(event.src_path)
        t = Timer(0.200, self.upload)
        t.start()


def watch_command(env, directory):
    if directory is None:
        directory = '.'

    cartridges = collect_cartridges(directory)

    print(f"{Fore.GREEN}Watching {directory}; Uploading to {env['server']} " +
          f"code version {env['codeVersion']}{Fore.RESET}")

    observer = Observer()
    for cartridge_path, cartridge_name in cartridges:
        print(f"Watching {cartridge_name}")
        webdav_event_handler = SFCCWebdavUploaderEventHandler(env, cartridge_path, cartridge_name)
        observer.schedule(webdav_event_handler, cartridge_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
