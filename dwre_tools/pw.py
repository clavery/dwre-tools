from __future__ import print_function
import sys

import requests
from colorama import Fore, Back, Style
import keyring

from .env import load_config, save_config, get_environment
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
            print("Login https://{0}@{1}/on/demandware.store/Sites-Site/".format(e.get('username'), e.get('server')), end=' ')
            if e.get('useAccountManager'):
                print(Fore.GREEN + "[ACCOUNT MANAGER SSO]" + Fore.RESET)
                continue
            try:
                session = requests.session()
                session.verify = e.get("verify", True)
                if 'clientcert' in e:
                    session.cert = (e["clientcert"], e["clientkey"])

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
                env = get_environment(env_name, p)
                break

    if env:
        if not env.get('password'):
            key = "dwre-%s" % (env["server"])
            if env.get('useAccountManager'):
                key = "dwre-account-manager"
            keyring.set_password(key, env["username"], password)
            print("Updated %s [KEYCHAIN]" % account_name)
        else:
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
            env = get_environment(env_name, p)
            extra = "https://%s@%s/on/demandware.store/Sites-Site/" % (
                env.get("username"), env.get("server"))

            if not env.get('password'):
                key = "dwre-%s" % (env["server"])
                if env.get('useAccountManager'):
                    key = "dwre-account-manager"
                keyring_password = keyring.get_password(key, env["username"])
                env["password"] = keyring_password

            account = {"account_name": name,
                       "extra": extra,
                       "username": env.get("username"),
                       "password": env.get("password")}
            hosts.append(account)
            hosts_by_name[name] = account
    return hosts, hosts_by_name
