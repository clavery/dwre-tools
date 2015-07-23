import requests
import pyquery
import time


def get_current_versions(env, session):
    versions_url = "https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-Versions".format(env["server"])
    response = session.get(versions_url)

    if "application/json" not in response.headers['content-type']:
        raise RuntimeError("Server response is not json; this requires manual intervention")
    else:
        tool_version = response.json()["toolVersion"]
        migration_version = response.json()["migrationVersion"]
        bootstrap_required = response.json()["missingToolVersion"]
        current_migration_path = None
        if "migrationPath" in response.json() and response.json()["migrationPath"]:
            current_migration_path = response.json()["migrationPath"].split(',')
        return (tool_version, migration_version, current_migration_path)


def login_business_manager(env, session):
    response = session.post("https://{}/on/demandware.store/Sites-Site/default/ViewApplication-ProcessLogin".format(env["server"]),
                            data=dict(
                                LoginForm_Login=env["username"],
                                LoginForm_Password=env["password"],
                                LocaleID="",
                                LoginForm_RegistrationDomain="Sites",
                                login=""))
    if "Invalid login or password" in response.content:
        raise RuntimeError("Invalid login or password")


def wait_for_import(env, session, filename):
    time.sleep(0.5)
    response = session.get("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Status".format(env["server"]))
    response_q = pyquery.PyQuery( response.content)
    log_link = response_q.find("a:contains('Site Import'):contains('%s')" % filename).eq(0).attr("href")
    if not log_link:
        raise Exception("Failure to find status link for %s. Check import log." % filename)
    finished = False
    while not finished:
        log_response = session.get(log_link)
        if "finished successfully" in log_response.content:
            finished = True
        elif "aborted" in log_response.content:
            raise RuntimeError("Failure to import %s. Check import log." % filename)
        else:
            time.sleep(2)

