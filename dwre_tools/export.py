from __future__ import print_function

import json
from collections import defaultdict
import time

from flask import Flask, request, render_template
import requests
import webbrowser
import yaml
import re
import tempfile
import uuid
import zipfile, io
import os
import shutil

from .bmtools import login_business_manager, get_list_data_units, get_export_zip, authenticate_webdav_session, \
    authenticate_session_from_env


def get_sites(env, session):
    resp = session.get("https://{}/s/-/dw/data/v20_8/sites".format(env["server"]))
    if resp.status_code != 200:
        return []  # no sites access
    return map(lambda s: s.get("id"), resp.json().get('data'))


def get_catalogs(env, session):
    resp = session.get("https://{}/s/-/dw/data/v20_8/catalogs".format(env["server"]))
    if resp.status_code != 200:
        return []  # no sites access
    return list(map(lambda s: s.get("id"), resp.json().get('data')))


def get_site_specific_units(site):
    return [{
        "id": "sites|" + site + "|ab_tests",
        "text": "A/B Tests",
    },
        {"id": "sites|" + site + "|active_data_feeds", "text": "Active Data Feeds.", },
        {"id": "sites|" + site + "|cache_settings", "text": "Cache Settings.", },
        {"id": "sites|" + site + "|campaigns_and_promotions", "text": "Campaigns and Promotions.", },
        {"id": "sites|" + site + "|content", "text": "Content.", },
        {"id": "sites|" + site + "|coupons", "text": "Coupons.", },
        {"id": "sites|" + site + "|custom_objects", "text": "Custom Objects.", },
        {"id": "sites|" + site + "|customer_cdn_settings", "text": "Customer CDN Settings.", },
        {"id": "sites|" + site + "|customer_groups", "text": "Customer Groups.", },
        {"id": "sites|" + site + "|distributed_commerce_extensions", "text": "Distributed Commerce Extensions.", },
        {"id": "sites|" + site + "|dynamic_file_resources", "text": "Dynamic File Resources.", },
        {"id": "sites|" + site + "|gift_certificates", "text": "Gift Certificates.", },
        {"id": "sites|" + site + "|ocapi_settings", "text": "OCAPI Settings.", },
        {"id": "sites|" + site + "|payment_methods", "text": "Payment Methods.", },
        {"id": "sites|" + site + "|payment_processors", "text": "Payment Processors.", },
        {"id": "sites|" + site + "|redirect_urls", "text": "Redirect URLs.", },
        {"id": "sites|" + site + "|search_settings", "text": "Search Settings.", },
        {"id": "sites|" + site + "|shipping", "text": "Shipping.", },
        {"id": "sites|" + site + "|site_descriptor", "text": "Site Descriptor.", },
        {"id": "sites|" + site + "|site_preferences", "text": "Site Preferences.", },
        {"id": "sites|" + site + "|sitemap_settings", "text": "Sitemap Settings.", },
        {"id": "sites|" + site + "|slots", "text": "Slots.", },
        {"id": "sites|" + site + "|sorting_rules", "text": "Sorting Rules.", },
        {"id": "sites|" + site + "|source_codes", "text": "Source Codes.", },
        {"id": "sites|" + site + "|static_dynamic_alias_mappings", "text": "Static, Dynamic and Alias mappings.", },
        {"id": "sites|" + site + "|stores", "text": "Stores.", },
        {"id": "sites|" + site + "|tax", "text": "Tax.", },
        {"id": "sites|" + site + "|url_rules", "text": "URL Rules.", },
    ]


def get_global_units():
    return [{
        "id": "global_data|access_roles",
        "text": "Access Roles",
    },
    {"id": "global_data|csc_settings", "text": "Settings for Customer Service Center customization.", },
    {"id": "global_data|csrf_whitelists", "text": "CSRF Allowlists.", },
    {"id": "global_data|custom_preference_groups", "text": "Global Preferences", },
    {"id": "global_data|custom_quota_settings", "text": "Custom quota settings of the instance.", },
    {"id": "global_data|custom_types", "text": "Custom Types (Meta Data).", },
    {"id": "global_data|geolocations", "text": "Geolocations of the organization.", },
    {"id": "global_data|global_custom_objects", "text": "Global custom objects.", },
    {"id": "global_data|job_schedules", "text": "Scheduled job definitions.", },
    {"id": "global_data|job_schedules_deprecated", "text": "Deprecated scheduled job definitions.", },
    {"id": "global_data|locales", "text": "Locales.", },
    {"id": "global_data|meta_data", "text": "System object type extensions and custom object type extensions.", },
    {"id": "global_data|oauth_providers", "text": "OAuth providers.", },
    {"id": "global_data|ocapi_settings", "text": "Global OCAPI settings.", },
    {"id": "global_data|page_meta_tags", "text": "Page meta tag definitions.", },
    {"id": "global_data|preferences", "text": "Global preferences.", },
    {"id": "global_data|price_adjustment_limits", "text": "Price adjustment limits for all roles.", },
    {"id": "global_data|services", "text": "Service definitions from the service framework.", },
    {"id": "global_data|sorting_rules", "text": "Global sorting rules.", },
    {"id": "global_data|static_resources", "text": "Global static resources.", },
    {"id": "global_data|system_type_definitions", "text": "System Type Definitions (Meta Data).", },
    {"id": "global_data|users", "text": "Users of the organization.", },
    {"id": "global_data|webdav_client_permissions", "text": "Global WebDAV Client Permissions.", },]


def get_export_data_units(env):
    session = requests.session()
    authenticate_session_from_env(env, session)
    sites = get_sites(env, session)
    catalogs = get_catalogs(env, session)

    data_units = [
        {
            "id": "catalog_static_resources|all",
            "text": "Catalog Static Resources",
            "children": map(lambda c: ({
                "id": "catalog_static_resources|" + c,
                "text": c
            }), catalogs)
        },
        {
            "id": "catalogs|all",
            "text": "Catalogs",
            "children": map(lambda c: ({
                "id": "catalogs|" + c,
                "text": c
            }), catalogs)
        },
        {
            "id": "libraries|all",
            "text": "Libraries",
        },
        {
            "id": "library_static_resources|all",
            "text": "Library Static Resources",
        },
        {
            "id": "inventory_lists|all",
            "text": "Inventory Lists",
        },
        {
            "id": "customer_lists|all",
            "text": "Customer Lists",
        },
        {
            "id": "price_books|all",
            "text": "Price Books",
        },
    ]
    data_units.append({
        "id": "global_data|all",
        "text": "Global Data",
        "children": get_global_units()
    })
    site_units = {
        "id": "sites|all",
        "text": "Sites",
        "children": []
    }
    for s in sites:
        site_units["children"].extend([
            {
                "id": s + "|all",
                "text": s,
                "children": get_site_specific_units(s)
            }
        ])
    data_units.append(site_units)
    return data_units


def export_command(env, directory):
    print("Getting data units...")
    if "clientID" in env:
        use_ocapi = True
    if use_ocapi:
        data_units = get_export_data_units(env)
    else:
        bmsession = login_business_manager(env)
        data_units = get_list_data_units(env, bmsession)

    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app = Flask(__name__)

    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route("/")
    def index():
        return render_template('index.html', data_units=data_units)

    export_units = []
    cancelled = False

    @app.route("/config", methods=["POST"])
    def shutdown():
        if "cancel" in request.form:
            shutdown_server()
            cancelled = True
            return 'Canceled export...'
        else:
            for unit, value in request.form.items():
                if value == "on":
                    export_units.append(unit)
            shutdown_server()
            return 'Saving migration'

    webbrowser.open("http://localhost:5698")
    print("Launching web browser to http://localhost:5698")
    app.run(port=5698)

    if not cancelled:
        print("Exporting units:")
        [print("\t", u) for u in export_units]

        filename = "ToolsExport_" + str(uuid.uuid4()).replace("-", "")[:10]

        webdavsession = authenticate_webdav_session(env)

        if use_ocapi:
            data_unit_config = defaultdict(dict)
            for u in export_units:
                parts = u.split('|')
                parent = parts[0]
                subunits = parts[1:]

                _unit_config = data_unit_config[parent]
                _current_unit_config = _unit_config
                for i, subunit in enumerate(subunits):
                    if i == len(subunits) - 1:
                        _current_unit_config[subunit] = True
                    if subunit not in _current_unit_config:
                        _current_unit_config[subunit] = defaultdict(dict)
                    _current_unit_config = _current_unit_config[subunit]
                data_unit_config[parent] = _unit_config
            print(json.dumps(data_unit_config, indent=2))
            session = requests.session()
            authenticate_session_from_env(env, session)
            resp = session.post(
                "https://{}/s/-/dw/data/v20_8/jobs/sfcc-site-archive-export/executions".format(env["server"]), json={
                    "export_file": filename + ".zip",
                    "data_units": data_unit_config
                })
            resp.raise_for_status()
            j = resp.json()
            job_id = j.get("id")
            finished = False

            # try our best to find the link
            while not finished:
                time.sleep(2)
                resp = session.get(
                    "https://{}/s/-/dw/data/v20_8/jobs/sfcc-site-archive-export/executions/{}".format(env["server"],
                                                                                                      job_id))
                resp.raise_for_status()
                j = resp.json()
                exec_status = j.get("execution_status")
                log_file_name = j.get("log_file_name")
                status = j.get("status")
                if exec_status == "aborted" or status == "ERROR":
                    error = "Unknown"
                    if len(j.get("step_executions")) > 0:
                        error = j.get("step_executions")[0].get("exit_status").get("message")
                    raise RuntimeError(
                        "Failure to export %s. Check job execution log %s.\n%s" % (filename, log_file_name, error))
                elif exec_status == "finished":
                    finished = True
            dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip"
                        .format(env["server"], filename))
            resp = webdavsession.get(dest_url, stream=True)
            resp.raise_for_status()

            export_zip = zipfile.ZipFile(io.BytesIO(resp.content))
            resp = webdavsession.delete(dest_url)
            resp.raise_for_status()
        else:
            export_zip = get_export_zip(env, webdavsession, export_units, filename)

        tempdir = tempfile.mkdtemp()
        export_zip.extractall(tempdir)

        shutil.move(os.path.join(tempdir, filename), directory)

        print("Saved export to", directory)
