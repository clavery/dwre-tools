import os
import zipfile, io
import shutil

from colorama import Fore, Back, Style

import dwre_tools
from .utils import directory_to_zip
from .sync import collect_cartridges


def make_cartridge_package():
    bm_dwremigrate_path = os.path.join(dwre_tools.__path__[0], 'cartridges', 'bm_dwremigrate')
    return directory_to_zip(bm_dwremigrate_path, 'bm_dwremigrate')


def update_bm_cartridge_server(env, webdavsession):
    zip_file = make_cartridge_package()

    code_version = env['codeVersion']

    print("Syncing cartridge to code version {0}{1}{2} on {0}{3}{2}".format(Fore.YELLOW, code_version, Fore.RESET, env["server"]))
    dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/Cartridges/{1}/bm_dwremigrate.zip"
                .format(env["server"], code_version))
    response = webdavsession.put(dest_url, data=zip_file)
    response.raise_for_status()
    data = {"method" : "UNZIP"}
    response = webdavsession.post(dest_url, data=data)
    response.raise_for_status()
    response = webdavsession.delete(dest_url)
    response.raise_for_status()


def upgrade_bm_cartridge():
    cartridges = collect_cartridges('.')
    fresh_install = False

    bm_cartridges = [c[0] for c in cartridges if c[1] == 'bm_dwremigrate']
    if bm_cartridges:
        print(Fore.YELLOW + "Found cartridges in the following locations:")
        print(",".join(bm_cartridges) + Fore.RESET)
    else:
        print(Fore.RED + "Could not find bm_dwremigrate; will install to:")
        bm_cartridges = ["./bm_dwremigrate"]
        fresh_install = True
        print(",".join(bm_cartridges) + Fore.RESET)

    result = input("\nThis command will install the upgraded versions to the locations above. Are you sure (y/n)")
    if result not in ['Y', 'y']:
        print("Exiting.")
        return

    zip_file = make_cartridge_package()
    for cartridge_location in bm_cartridges:
        parent_path = os.path.join(cartridge_location, '..')
        if not fresh_install:
            shutil.rmtree(cartridge_location)
        zip_file.seek(0)

        zipf = zipfile.ZipFile(zip_file, 'r')
        zipf.extractall(parent_path)
        print(Fore.GREEN + "Updated " + cartridge_location + Fore.RESET)

