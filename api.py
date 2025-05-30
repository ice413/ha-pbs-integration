import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxmoxBackupAPI:
    def __init__(self, host, token_id, token_secret):
        self.base_url = f"https://{host}:8007/api2/json"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"PBSAPIToken={token_id}:{token_secret}"
        })

    def get_datastores(self):
        """Retrieve list of all datastores."""
        url = f"{self.base_url}/admin/datastore"
        resp = self.session.get(url, verify=False)
        resp.raise_for_status()
        return resp.json()

    def get_datastore_status(self, store_name):
        """Retrieve usage status of a specific datastore."""
        url = f"{self.base_url}/admin/datastore/{store_name}/status"
        resp = self.session.get(url, verify=False)
        resp.raise_for_status()
        return resp.json()

    def get_snapshots(self, store_name):
        """Retrieve all snapshots from a specific datastore."""
        url = f"{self.base_url}/admin/datastore/{store_name}/snapshots"
        resp = self.session.get(url, verify=False)
        resp.raise_for_status()
        return resp.json()