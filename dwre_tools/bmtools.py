from __future__ import print_function

import pyquery
import time
import json
import yaml
import re
import zipfile
import requests
import io
from urllib.parse import quote, urlencode, urlparse, parse_qs

from .exc import NotInstalledException

CSRF_FINDER = re.compile(r"'csrf_token'\s*,(?:\s|\n)*'(.*?)'", re.MULTILINE)
CSRF_FINDER2 = re.compile(r"csrf_token=(.*?)\"", re.MULTILINE)
OPENID_CONNECT_ENDPOINT = "/on/demandware.servlet/dw/oidc/openid_connect_login"
ACCOUNT_MANAGER_JSON_AUTHENTICATE = "https://account.demandware.com/dwsso/json/realms/root/authenticate"
ACCOUNT_MANAGER_COOKIE_NAME = "dwAccountManager"
BM_SESSION_CACHE = dict()

def update_hotfix_path(env, path):
    use_ocapi = False
    if "clientID" in env:
        use_ocapi = True

    if use_ocapi:
        instance_type = "development"
        if "instanceType" in env:
            instance_type = env["instanceType"]
        session = requests.session()
        authenticate_session_from_env(env, session)
        resp = session.patch("https://{}/s/-/dw/data/v20_8/global_preferences/preference_groups/dwreMigrate/{}".format(env["server"], instance_type), json={
            "c_dwreMigrateHotfixes": path
        })
        resp.raise_for_status()
    else:
        bmsession = login_business_manager(env)
        response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateVersion".format(env["server"]),
                                  data={"dwreMigrateHotfixes" : path})
        response.raise_for_status()


def update_current_version(env, id, path):
    use_ocapi = False
    if "clientID" in env:
        use_ocapi = True

    if use_ocapi:
        instance_type = "development"
        if "instanceType" in env:
            instance_type = env["instanceType"]
        session = requests.session()
        authenticate_session_from_env(env, session)
        resp = session.patch("https://{}/s/-/dw/data/v20_8/global_preferences/preference_groups/dwreMigrate/{}".format(env["server"], instance_type), json={
            "c_dwreMigrateCurrentVersion": id,
            "c_dwreMigrateVersionPath": path
        })
        resp.raise_for_status()
    else:
        bmsession = login_business_manager(env)
        response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateVersion".format(env["server"]),
                                  data={"NewVersion" : id, "NewVersionPath" : path})
        response.raise_for_status()


def get_current_versions(env):
    use_ocapi = False
    if "clientID" in env:
        use_ocapi = True

    if use_ocapi:
        instance_type = "development"
        if "instanceType" in env:
            instance_type = env["instanceType"]
        session = requests.session()
        authenticate_session_from_env(env, session)
        resp = session.get("https://{}/s/-/dw/data/v20_8/global_preferences/preference_groups/dwreMigrate/{}".format(env["server"], instance_type))
        resp.raise_for_status()
        j = resp.json()
        return (
            j.get("c_dwreMigrateToolVersion"),
            j.get("c_dwreMigrateCurrentVersion"),
            j.get("c_dwreMigrateVersionPath").split(","),
            "2",
            j.get("c_dwreMigrateHotfixes").split(',')
        )
    else:
        bmsession = login_business_manager(env)

        versions_url = ("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-Versions"
                        .format(env["server"]))
        response = bmsession.get(versions_url)

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


# Authenticate a session using account manager client credentials
def authenticate_session_from_env(env, session):
    auth = (env["clientID"], env["clientPassword"])
    resp = requests.post("https://account.demandware.com/dwsso/oauth2/access_token", data={"grant_type":"client_credentials"}, auth=auth)
    resp.raise_for_status()
    j = resp.json()
    access_token = j.get("access_token")
    expiration_seconds = j.get("expires_in");
    session.headers.update({"Authorization": "Bearer " + access_token})
    session.headers.update({"x-dw-client-id": env["clientID"]})


def authenticate_webdav_session(env):
    session = requests.session()
    session.verify = env["verify"]
    session.cert = env["cert"]

    use_ocapi = False
    if "clientID" in env:
        use_ocapi = True

    if use_ocapi:
        authenticate_session_from_env(env, session)
    else:
        session.auth = (env["username"], env["password"])
    return session


def login_via_account_manager(env):
    session = requests.session()
    session.verify = env["verify"]
    session.cert = env["cert"]
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
        "X-OpenAM-Password": env["password"],
        "Accept-API-Version" : "protocol=1.0,resource=2.1",
        "Content-Type": "application/json"
    }

    """
    New series of "callback" based assertions: https://backstage.forgerock.com/docs/am/6.5/AM-6.5-Dev-Guide.pdf
    """
    params = {
        "ForceAuth": "true",
        "goto" : redirect
    }
    resp = session.post(ACCOUNT_MANAGER_JSON_AUTHENTICATE, json=data, headers=headers, params=params)
    resp.raise_for_status()
    authid = resp.json().get('authId')

    data = {
        "authId": authid,
        "callbacks": [
            {
                "type": "NameCallback",
                "output": [
                    {
                        "name": "prompt",
                        "value": "User Name"
                    }
                ],
                "input": [
                    {
                        "name": "IDToken1",
                        "value": env["username"]
                    }
                ]
            },
            {
                "type": "TextOutputCallback",
                "output": [
                    {
                        "name": "message",
                        "value": "var pwdinp = document.createElement('input');\npwdinp.id='shadowPassword';\npwdinp.name='shadowPassword';\npwdinp.type='password';\npwdinp.tabindex='-1';\npwdinp.style='visibility:hidden';\ndocument.querySelector('form').appendChild(pwdinp);\n"
                    },
                    {
                        "name": "messageType",
                        "value": "4"
                    }
                ]
            }
        ]
    }
    resp = session.post(ACCOUNT_MANAGER_JSON_AUTHENTICATE, json=data, headers=headers, params=params)
    authid = resp.json().get('authId')
    resp.raise_for_status()

    data = {
        "authId": authid,
        "callbacks": [
            {
                "type": "NameCallback",
                "output": [
                    {
                        "name": "prompt",
                        "value": "User Name"
                    }
                ],
                "input": [
                    {
                        "name": "IDToken1",
                        "value": env['username']
                    }
                ]
            },
            {
                "type": "PasswordCallback",
                "output": [
                    {
                        "name": "prompt",
                        "value": "Password"
                    }
                ],
                "input": [
                    {
                        "name": "IDToken2",
                        "value": env['password']
                    }
                ]
            },
            {
                "type": "TextOutputCallback",
                "output": [
                    {
                        "name": "message",
                        "value": "var pwdinp = document.createElement('input');\npwdinp.id='shadowPassword';\npwdinp.name='shadowPassword';\npwdinp.type='password';\npwdinp.tabindex='-1';\npwdinp.style='visibility:hidden';\ndocument.querySelector('form').appendChild(pwdinp);\n\ndocument.querySelector('div.form-group').style.visibility='hidden'; // hide username and first pwd field\ndocument.querySelector('form').appendChild(document.querySelector('div.form-group')); // move to end so there is no gap before password field\ndocument.querySelector('#idToken2').addEventListener('input',function() {\n    document.querySelector('#shadowPassword').value=this.value;\n    return true;\n}); // copy value to shadow pwd field\ndocument.querySelector('#idToken2').focus();\n"
                    },
                        {
                            "name": "messageType",
                            "value": "4"
                        }
                ]
            }
        ]
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
    resp = session.get(success_url, allow_redirects=False, headers=headers, params=params)
    resp.raise_for_status()

    redirect_url = resp.headers.get('location')

    resp = session.get(redirect_url)
    resp.raise_for_status()

    csrf_match = CSRF_FINDER.search(resp.text)
    if not csrf_match:
        csrf_match = CSRF_FINDER2.search(resp.text)

    if csrf_match:
        csrf_token = csrf_match.group(1)
        session.params['csrf_token'] = csrf_token
        session.headers['origin'] = "https://%s" % env["server"]
    else:
        print(resp.text)
        raise RuntimeError("Can't find CSRF")
    return session


def login_business_manager(env):
    global BM_SESSION_CACHE
    session = requests.session()
    session.verify = env["verify"]
    session.cert = env["cert"]
    if env["server"] in BM_SESSION_CACHE:
        return BM_SESSION_CACHE[env["server"]]

    if env.get('useAccountManager'):
        s = login_via_account_manager(env)
        BM_SESSION_CACHE[env["server"]] = s
        return s

    response = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewApplication-ProcessLogin".format(env["server"]),
                            data=dict(
                                LoginForm_Login=env["username"],
                                LoginForm_Password=env["password"],
                                LocaleID="",
                                LoginForm_RegistrationDomain="Sites",
                                login=""), timeout=10)
    response.raise_for_status()

    if 'redirectform' in response.text:
        s = login_via_account_manager(env)
        BM_SESSION_CACHE[env["server"]] = s
        return s

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

    BM_SESSION_CACHE[env["server"]] = session
    return session


def select_site(env, session, site_uuid):
    data = {
        "SelectedSiteID": site_uuid
    }
    resp = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewApplication-SelectSite?MenuGroupID=ChannelMenu&ChannelID="
                        .format(env["server"]), data=data)
    resp.raise_for_status()


def activate_code_version(env, code_version):
    use_ocapi = False
    if "clientID" in env:
        use_ocapi = True

    if use_ocapi:
        session = requests.session()
        authenticate_session_from_env(env, session)
        resp = session.patch("https://{}/s/-/dw/data/v20_8/code_versions/{}".format(env["server"], code_version), json={
            "active": True
        })
        resp.raise_for_status()
        print(resp.json())
    else:
        bmsession = login_business_manager(env)
        bmsession.post("https://{}/on/demandware.store/Sites-Site/default/ViewCodeDeployment-Activate"
                       .format(env["server"]), data=dict(
                           CodeVersionID=code_version))


def import_site_package(env, filename):
    use_ocapi = False
    if "clientID" in env:
        use_ocapi = True

    if use_ocapi:
        session = requests.session()
        authenticate_session_from_env(env, session)
        resp = session.post("https://{}/s/-/dw/data/v20_8/jobs/sfcc-site-archive-import/executions".format(env["server"]), json={
            "file_name": filename + ".zip"
        })
        resp.raise_for_status()
        j = resp.json()
        job_id = j.get("id")
        finished = False

        # try our best to find the link
        while not finished:
            time.sleep(2)
            resp = session.get("https://{}/s/-/dw/data/v20_8/jobs/sfcc-site-archive-import/executions/{}".format(env["server"], job_id))
            resp.raise_for_status()
            j = resp.json()
            exec_status = j.get("execution_status")
            log_file_name = j.get("log_file_name")
            status = j.get("status")
            if exec_status == "aborted" or status == "ERROR":
                error = "Unknown"
                if len(j.get("step_executions")) > 0:
                    error = j.get("step_executions")[0].get("exit_status").get("message")
                raise RuntimeError("Failure to import %s. Check job execution log %s.\n%s" % (filename, log_file_name, error))
            elif exec_status == "finished":
                finished = True
    else:
        bmsession = login_business_manager(env)

        response = bmsession.post(
            "https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Dispatch".format(env["server"]),
            data={"import": "", "ImportFileName": filename + ".zip", "realmUse": "False"})
        response.raise_for_status()

        wait_for_import(env, bmsession, filename)


def wait_for_import(env, session, filename):
    log_link = None
    retries = 0

    # try our best to find the link
    while not log_link and retries < 600:
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


def export_data_units(env, units, filename):
    session = login_business_manager(env)
    data = [ ('SelectedExportUnit', u) for u in units ]
    data.append( ('export', '') )
    data.append( ('exportFile', filename) )

    resp = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Dispatch".format(env["server"]),
                        data=data)
    resp.raise_for_status()


def wait_for_export(env, filename):
    log_link = None
    retries = 0

    session = login_business_manager(env)

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


def get_export_zip(env, webdavsession, export_units, filename):
    export_data_units(env, export_units, filename)
    wait_for_export(env, filename)

    dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip"
                .format(env["server"], filename))
    resp = webdavsession.get(dest_url, stream=True)
    resp.raise_for_status()

    zip_file = zipfile.ZipFile(io.BytesIO(resp.content))
    resp = webdavsession.delete(dest_url)
    resp.raise_for_status()
    return zip_file


def get_install_export_zip(env, webdavsession, filename):
    if "clientID" in env:
        use_ocapi = True
    if use_ocapi:
        # TODO
        pass
    else:
        zip_file = get_export_zip(env, webdavsession,
                                  export_units=["AccessRoleExport", "GlobalPreferencesExport"],
                                  filename=filename)
        return zip_file
