from __future__ import print_function
import sys

import requests
from colorama import Fore, Back, Style

from .env import load_config, save_config
from .bmtools import login_business_manager


def pw_list():
    hosts, _ = get_dwre_hosts()
    for a in hosts:
        print(a.get("account_name"))


def pw_get(account_name):
    _, hosts_by_name = get_dwre_hosts()
    host = hosts_by_name.get(account_name)

    print(host.get('password'), end='')
    print(host.get('extra'), file=sys.stderr)


def pw_refresh():
    j = load_config()
    for project_name, p in j.get('projects').items():
        for env_name, e in p.get('environments').items():
            try:
                session = requests.session()
                session.verify = e.get("verify", True)
                if 'clientcert' in e:
                    session.cert = (e["clientcert"], e["clientkey"])

                print("Login https://{0}@{1}/on/demandware.store/Sites-Site/".format(e.get('username'), e.get('server')), end=' ')
                login_business_manager(e, session)
                print(Fore.GREEN + "[SUCCESS]" + Fore.RESET)
            except requests.exceptions.ReadTimeout as e:
                print(Fore.RED + "[FAILED: Timeout. Dead instance?]".format(e) + Fore.RESET)
            except requests.exceptions.ConnectionError as e:
                print(Fore.RED + "[FAILED: Dead instance? {}]".format(e) + Fore.RESET)
            except requests.exceptions.SSLError as e:
                print(Fore.RED + "[FAILED: {}]".format(e) + Fore.RESET)
            except RuntimeError as e:
                print(Fore.RED + "[FAILED: {}]".format(e) + Fore.RESET)



def pw_put(account_name, password):
    j = load_config()
    env = None

    for project_name, p in j.get('projects').items():
        for env_name, e in p.get('environments').items():
            name = "%s-%s" % (project_name, env_name)
            if account_name == name:
                env = e
                break

    if env:
        env['password'] = password
        save_config(j)
        print("Updated %s" % account_name)


def get_dwre_hosts():
    hosts = []
    hosts_by_name = {}

    j = load_config()
    for project_name, p in j.get('projects').items():
        for env_name, e in p.get('environments').items():
            name = "%s-%s" % (project_name, env_name)
            extra = "https://%s@%s/on/demandware.store/Sites-Site/" % (
                e.get("username"), e.get("server"))
            account = {"account_name": name,
                       "extra": extra,
                       "username": e.get("username"),
                       "password": e.get("password")}
            hosts.append(account)
            hosts_by_name[name] = account
    return hosts, hosts_by_name
