import requests

class ProxmoxBackupAPI:
    def __init__(self, host, username, password):
        self.base_url = f"https://{host}:8007/api2/json"
        self.session = requests.Session()
        self._login(username, password)

    def _login(self, username, password):
        url = f"{self.base_url}/access/ticket"
        data = {"username": username, "password": password}
        resp = self.session.post(url, data=data, verify=False)
        resp.raise_for_status()
        ticket = resp.json()["data"]["ticket"]
        csrf = resp.json()["data"]["CSRFPreventionToken"]
        self.session.cookies.set("PBSAuthCookie", ticket)
        self.session.headers.update({"CSRFPreventionToken": csrf})

    def get_datastores(self):
        url = f"{self.base_url}/admin/datastore"
        resp = self.session.get(url, verify=False)
        resp.raise_for_status()
        return resp.json()["data"]