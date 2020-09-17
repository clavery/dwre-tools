from __future__ import print_function

try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

import requests
from colorama import Fore, Back, Style

from .bmtools import login_business_manager


def reindex(env):
    bmsession = login_business_manager(env)

    response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateIndexes".format(env["server"]))
    response.raise_for_status()

    return True


def reindex_command(env):
    try:
        reindex(env)
        print(Fore.GREEN + "Initiated reindex on {0}".format(env['server']) + Fore.RESET)
    except HTTPError as e:
        print(Fore.RED + "Error reindexing: {}".format(e.message) + Fore.RESET)
        return False

