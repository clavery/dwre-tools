from __future__ import print_function

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

from .bmtools import login_business_manager, get_list_data_units, export_data_units, wait_for_export


def export_command(env, directory):
    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    print("Getting data units from business manager...")
    login_business_manager(env, bmsession)
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
            for unit,value in request.form.items():
                if value == "on":
                    export_units.append(unit)
            shutdown_server()
            return 'Saving migration'

    webbrowser.open("http://localhost:5698")
    app.run(port=5698)

    if not cancelled:
        print("Exporting units:")
        [print("\t", u) for u in export_units]

        filename = "ToolsExport_" + str(uuid.uuid4()).replace("-", "")[:10]
        export_data_units(env, bmsession, export_units, filename)
        wait_for_export(env, bmsession, filename)

        webdavsession = requests.session()
        webdavsession.verify = env["verify"]
        webdavsession.auth=(env["username"], env["password"],)
        webdavsession.cert = env["cert"]

        dest_url = ("https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip"
                    .format(env["server"], filename))
        resp = webdavsession.get(dest_url, stream=True)
        resp.raise_for_status()

        tempdir = tempfile.mkdtemp()

        export_zip = zipfile.ZipFile(io.BytesIO(resp.content))
        export_zip.extractall(tempdir)

        shutil.move(os.path.join(tempdir, filename), directory)

        resp = webdavsession.delete(dest_url)
        resp.raise_for_status()

        print("Saved export to", directory)
