import datetime

import requests

CLIENT_IDENTIFIER = "dwre-tools"
OCAPI_VERSION = "v18_6"

WEBDAV_CARTRIDGES = "/on/demandware.servlet/webdav/Sites/Cartridges/"
WEBDAV_IMPEX_INSTANCE = "/on/demandware.servlet/webdav/Sites/Impex/src/instance/"
WEBDAV_LOGS = "/on/demandware.servlet/webdav/Sites/Logs/"
BM_IMPEX_IMPORT = "/on/demandware.store/Sites-Site/default/ViewSiteImpex-Dispatch"
BM_IMPEX_STATUS = "/on/demandware.store/Sites-Site/default/ViewCodeDeployment-Activate"
BM_CODE_ACTIVATE = "/on/demandware.store/Sites-Site/default/ViewCodeDeployment-Activate"


class SFCCInstance():
    """Encapsulates SFCC instance operations (BM, OCAPI, WebDAV)

    This class will use the best possible method for communication and file transfer
    given the provided configuration and instance capabilities/access.
    """

    def __init__(self, server, username=None, password=None, code_version=None,
                 client_id=None, client_password=None, verify=True, cert=None):
        self.server = server
        self.username = username
        self.password = password
        self.code_version = code_version
        self.client_id = client_id
        self.client_password = client_password

        self.bmsession = None
        self.webdavsession = None
        self.access_token = None
        self.access_token_expiration = None

    @classmethod
    def from_env(cls, env):
        """Create an SFCCInstance instance from a dwre.json/dw.json env"""
        return cls(env.get('server'),
                   username=env.get('username'),
                   password=env.get('password'),
                   client_id=env.get('clientId'),
                   client_password=env.get('clientPassword'),
                   code_version=env.get('codeVersion'),
                   cert=env.get('cert'),
                   verify=env.get('verify', True))


