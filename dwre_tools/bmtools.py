from __future__ import print_function

import pyquery
import time
import yaml
import re
import zipfile
import io
from urllib.parse import quote, urlencode, urlparse, parse_qs

from .exc import NotInstalledException

CSRF_FINDER = re.compile(r"'csrf_token'\s*,(?:\s|\n)*'(.*?)'", re.MULTILINE)
OPENID_CONNECT_ENDPOINT = "/on/demandware.servlet/dw/oidc/openid_connect_login"
ACCOUNT_MANAGER_JSON_AUTHENTICATE = "https://account.demandware.com/dwsso/json/realms/root/authenticate"
ACCOUNT_MANAGER_COOKIE_NAME = "dwAccountManager"


def get_current_versions(env, session):
    versions_url = ("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-Versions"
                    .format(env["server"]))
    response = session.get(versions_url)

    if "application/json" not in response.headers['content-type']:
        raise NotInstalledException("Server response is not json;" +
                                    "DWRE Tools is likely not installed")
    else:
        tool_version = response.json()["toolVersion"]
        migration_version = response.json()["migrationVersion"]
        cartridge_version = response.json().get('cartridgeVersion')
        current_migration_path = None
        hotfixes = []
        if "migrationPath" in response.json() and response.json()["migrationPath"]:
            current_migration_path = response.json()["migrationPath"].split(',')
        if "dwreMigrateHotfixes" in response.json() and response.json()["dwreMigrateHotfixes"]:
            hotfixes = response.json()["dwreMigrateHotfixes"].split(',')
        return (tool_version, migration_version, current_migration_path,
                cartridge_version, hotfixes)



def login_via_account_manager(env, session):
    data = dict(
        source='LOGIN_DEFAULT',
        supportLogin='true',
        amLogin='true'
    )
    resp = session.post(f"https://{env['server']}{OPENID_CONNECT_ENDPOINT}", data=data, allow_redirects=False)
    resp.raise_for_status()
    redirect_location = resp.headers.get('location')
    assert(redirect_location)
    query_string = parse_qs(urlparse(redirect_location).query, keep_blank_values=True)

    # Do not prompt for oauth permissions; implicit allow
    if 'prompt' in query_string:
        del query_string['prompt']
    query_string['decision'] = "Allow"
    redirect = "https://account.demandware.com/dwsso/oauth2/authorize?" + urlencode(query_string, doseq=True)

    # login to forgerock AM via restful interface to obtain token
    headers = {
        "X-OpenAM-Username": env["username"],
        "X-OpenAM-Password": env["password"]
    }
    data = {
    }
    params = {
        "goto": redirect # not entirely necessary but may be useful for auditing
    }

    resp = session.post(ACCOUNT_MANAGER_JSON_AUTHENTICATE, json=data, headers=headers, params=params)
    resp.raise_for_status()

    token = resp.json().get('tokenId')
    success_url = resp.json().get('successUrl')

    # obtain access token to sandbox via restfully obtained tokenid
    headers = {
        ACCOUNT_MANAGER_COOKIE_NAME: token,
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie" : "%s=%s" % (ACCOUNT_MANAGER_COOKIE_NAME, token)
    }
    resp = session.get(success_url, allow_redirects=False, headers=headers)
    resp.raise_for_status()

    redirect_url = resp.headers.get('location')

    resp = session.get(redirect_url)
    resp.raise_for_status()

    csrf_match = CSRF_FINDER.search(resp.text)

    if csrf_match:
        csrf_token = csrf_match.group(1)
        session.params['csrf_token'] = csrf_token
        session.headers['origin'] = "https://%s" % env["server"]
    else:
        print(response.text)
        raise RuntimeError("Can't find CSRF")


def login_business_manager(env, session):
    if env.get('useAccountManager'):
        return login_via_account_manager(env, session)

    response = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewApplication-ProcessLogin".format(env["server"]),
                            data=dict(
                                LoginForm_Login=env["username"],
                                LoginForm_Password=env["password"],
                                LocaleID="",
                                LoginForm_RegistrationDomain="Sites",
                                login=""), timeout=10)
    response.raise_for_status()

    if 'redirectform' in response.text:
        return login_via_account_manager(env, session)

    if "Please create a new password." in response.text:
        raise RuntimeError("Password Expired; New password required")

    if "Invalid login or password" in response.text:
        raise RuntimeError("Invalid login or password")

    if "This user is currently inactive.<br />Please contact the administrator." in response.text:
        raise RuntimeError("Inactive account")

    csrf_match = CSRF_FINDER.search(response.text)

    if csrf_match:
        csrf_token = csrf_match.group(1)
        session.params['csrf_token'] = csrf_token
        session.headers['origin'] = "https://%s" % env["server"]
    else:
        raise RuntimeError("Can't find CSRF")

    # ccdx check for merge request and skip
    if "Log In Without Linking Accounts" in response.text and "skipMerge" in response.text:
        response = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewLogin-ProcessMerge".format(env["server"]),
                                data=dict(
                                    source="MERGE_ON_LOGIN",
                                    skipMerge='',), timeout=10)
        response.raise_for_status()

    csrf_match = CSRF_FINDER.search(response.text)

    if csrf_match:
        csrf_token = csrf_match.group(1)
        session.params['csrf_token'] = csrf_token
        session.headers['origin'] = "https://%s" % env["server"]
    else:
        print(response.text)
        raise RuntimeError("Can't find CSRF")

def select_site(env, session, site_uuid):
    data = {
        "SelectedSiteID": site_uuid
    }
    resp = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewApplication-SelectSite?MenuGroupID=ChannelMenu&ChannelID="
                        .format(env["server"]), data=data)
    resp.raise_for_status()


def activate_code_version(env, session, code_version):
    session.post("https://{}/on/demandware.store/Sites-Site/default/ViewCodeDeployment-Activate"
                 .format(env["server"]), data=dict(
                     CodeVersionID=code_version))


def wait_for_import(env, session, filename):
    log_link = None
    retries = 0

    # TODO detect import in progress

    # try our best to find the link
    while not log_link and retries < 300:
        time.sleep(1)
        response = session.get("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Status".format(env["server"]))
        response_q = pyquery.PyQuery(response.content)
        log_link = response_q.find("a:contains('Site Import'):contains('%s')" % filename).eq(0).attr("href")
        retries = retries + 1
    if not log_link:
        raise Exception("Failure to find status link for %s. Check import log." % filename)
    finished = False
    while not finished:
        log_response = session.get(log_link)
        if "finished successfully" in log_response.text:
            finished = True
        elif "aborted" in log_response.text:
            raise RuntimeError("Failure to import %s. Check import log." % filename)
        else:
            time.sleep(2)


EXPORT_UNIT_JSON_OLD = re.compile(r"var exportUnitJSON = (.*?)/\*\*", re.MULTILINE | re.DOTALL)
EXPORT_UNIT_JSON = re.compile(r"var exportUnitJSON1 = (?=\[)(?P<json>.*?)// too big",
                              re.MULTILINE | re.DOTALL)
EXPORT_UNIT_BREAK = re.compile(r"\][\w\n]*?var exportUnitJSON2 = \[", re.MULTILINE | re.DOTALL)


def get_list_data_units(env, session):
    response = session.get("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Status".format(env["server"]))
    response.raise_for_status()
    match = EXPORT_UNIT_JSON.search(response.text)
    if not match:
        match = EXPORT_UNIT_JSON_OLD.search(response.text)
        if not match:
            raise Exception("Cannot load site impex page")
        group = match.group(1)
    else:
        group = EXPORT_UNIT_BREAK.sub(",", match.group("json"))
    data_units = yaml.safe_load(group)
    return data_units


def export_data_units(env, session, units, filename):
    data = [ ('SelectedExportUnit', u) for u in units ]
    data.append( ('export', '') )
    data.append( ('exportFile', filename) )

    resp = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Dispatch".format(env["server"]),
                        data=data)
    resp.raise_for_status()


def wait_for_export(env, session, filename):
    log_link = None
    retries = 0

    # try our best to find the link
    while not log_link and retries < 1000:
        time.sleep(1)
        response = session.get("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Status".format(env["server"]))
        response_q = pyquery.PyQuery(response.content)
        log_link = response_q.find("a:contains('Site Export'):contains('%s')" % filename).eq(0).attr("href")
        retries = retries + 1
    if not log_link:
        raise Exception("Failure to find status link for %s. Check import log." % filename)
    finished = False
    while not finished:
        log_response = session.get(log_link)
        if "finished successfully" in log_response.text:
            finished = True
        elif "aborted" in log_response.text:
            raise RuntimeError("Failure to import %s. Check import log." % filename)
        else:
            time.sleep(2)


def get_export_zip(env, bmsession, webdavsession, export_units, filename):
    export_data_units(env, bmsession, export_units, filename)
    wait_for_export(env, bmsession, filename)

    dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip"
                .format(env["server"], filename))
    resp = webdavsession.get(dest_url, stream=True)
    resp.raise_for_status()

    zip_file = zipfile.ZipFile(io.BytesIO(resp.content))
    resp = webdavsession.delete(dest_url)
    resp.raise_for_status()
    return zip_file
